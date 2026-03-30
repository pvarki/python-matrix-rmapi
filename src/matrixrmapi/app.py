"""Factory for the FastAPI app"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import filelock
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from libpvarki.logging import init_logging

from matrixrmapi import __version__
from .config import (
    LOG_LEVEL,
    SYNAPSE_BOT_USERNAME,
    SYNAPSE_REGISTRATION_SECRET,
    SYNAPSE_TOKEN_FILE,
    SYNAPSE_URL,
    get_manifest,
    get_server_domain,
)
from .api import all_routers, all_routers_v2
from .synapseutils.synapse_admin import SynapseAdmin

LOGGER = logging.getLogger(__name__)

# (key, alias_suffix, display_name, is_space, is_private)
_ROOMS_CONFIG: List[Tuple[str, str, str, bool, bool]] = [
    ("space", "{d}-space", "{d}", True, False),
    ("admin", "{d}-admin", "Admin channel", False, True),
    ("general", "{d}-general", "98-General-for-all", False, False),
    ("helpdesk", "{d}-helpdesk", "99-Helpdesk", False, False),
    ("offtopic", "{d}-offtopic", "Off topic", False, False),
]

_ROOM_TOPICS: Dict[str, str] = {
    "general": "Work discussion that does not fit any other room.",
    "helpdesk": "Report issues and get help from here.",
    "offtopic": "Everything that is not about the topics or work.",
}


async def _wait_for_synapse(synapse_url: str, retries: int = 60, interval: float = 5.0) -> bool:
    """Poll Synapse /health until it responds 200. Returns True on success."""
    LOGGER.info("Waiting for Synapse at %s ...", synapse_url)
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{synapse_url}/health", timeout=5.0)
                if resp.status_code == 200:
                    LOGGER.info("Synapse is ready")
                    return True
        except Exception:  # pylint: disable=broad-except  # nosec B110
            pass
        if attempt < retries - 1:
            await asyncio.sleep(interval)
    LOGGER.error("Synapse not reachable after %d attempts — integration disabled", retries)
    return False


async def _acquire_bot_token(synapse: SynapseAdmin) -> bool:
    """Acquire the admin bot token using a file lock for worker coordination."""
    lock_path = SYNAPSE_TOKEN_FILE.parent / "synapse_init.lock"
    lock = filelock.FileLock(str(lock_path))

    acquired = False
    try:
        lock.acquire(timeout=0.0)
        acquired = True
        # We are the init worker — register bot (idempotent: reads file if present)
        registration_secret = SYNAPSE_REGISTRATION_SECRET
        await synapse.setup(registration_secret, SYNAPSE_BOT_USERNAME, SYNAPSE_TOKEN_FILE)
        del registration_secret
        return True
    except filelock.Timeout:
        LOGGER.warning("Another worker is initialising the Synapse bot, waiting ...")
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Bot token acquisition failed: %s", exc)
        return False
    finally:
        if acquired:
            lock.release()

    # Non-init worker: wait for the token file to appear
    for _ in range(60):
        if SYNAPSE_TOKEN_FILE.exists():
            break
        await asyncio.sleep(2)
    else:
        LOGGER.error("Token file never appeared after waiting — integration disabled")
        return False

    # Load and validate the token written by the init worker
    try:
        await synapse.setup("", SYNAPSE_BOT_USERNAME, SYNAPSE_TOKEN_FILE)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Failed to load bot token from file: %s", exc)
        return False


async def _ensure_room(synapse: SynapseAdmin, name: str, alias: str, is_space: bool, is_private: bool) -> str:
    """Return room_id for alias, creating the room if it does not exist."""
    existing = await synapse.room_id_for_alias(alias)
    if existing:
        LOGGER.info("Room %s already exists: %s", alias, existing)
        return existing
    room_id = await synapse.create_room(name, alias, is_space=is_space, is_private=is_private)
    LOGGER.info("Created room %s -> %s", alias, room_id)
    return room_id


async def _ensure_rooms(synapse: SynapseAdmin, app: FastAPI, deployment: str, domain: str) -> None:
    """Create space and rooms if they don't exist; store IDs on app.state."""
    room_ids: Dict[str, str] = {}
    space_id: Optional[str] = None

    for key, alias_tpl, name_tpl, is_space, is_private in _ROOMS_CONFIG:
        alias = f"#{alias_tpl.format(d=deployment)}:{domain}"
        room_ids[key] = await _ensure_room(synapse, name_tpl.format(d=deployment), alias, is_space, is_private)
        if is_space:
            space_id = room_ids[key]

    if space_id:
        for key, room_id in room_ids.items():
            if key != "space":
                await synapse.add_child_to_space(space_id, room_id)

    app.state.rooms = room_ids
    LOGGER.info("Synapse rooms ready: %s", room_ids)


async def _configure_rooms_state(synapse: SynapseAdmin, rooms: Dict[str, str], deployment: str) -> None:
    """Apply join rules, encryption, history visibility, topics and names to all rooms.

    All state events are idempotent in Matrix — safe to re-apply on every restart.
    """
    name_by_key = {key: name_tpl.format(d=deployment) for key, _, name_tpl, _, _ in _ROOMS_CONFIG}
    space_id = rooms["space"]
    LOGGER.info("Applying room state configuration (idempotent)")
    for key, room_id in rooms.items():
        await synapse.set_room_state(room_id, "m.room.name", {"name": name_by_key[key]})
        if key == "space":
            await synapse.set_room_state(room_id, "m.room.join_rules", {"join_rule": "invite"})
            # Allow all space members to add child rooms (lower m.space.child to 0)
            levels = await synapse.get_power_levels(room_id)
            events_levels = dict(levels.get("events", {}))
            events_levels["m.space.child"] = 0
            levels["events"] = events_levels
            await synapse.set_room_state(room_id, "m.room.power_levels", levels)
            continue
        await synapse.set_room_state(room_id, "m.room.encryption", {"algorithm": "m.megolm.v1.aes-sha2"})
        await synapse.set_room_state(room_id, "m.room.history_visibility", {"history_visibility": "joined"})
        if key != "admin":
            await synapse.set_room_state(
                room_id,
                "m.room.join_rules",
                {"join_rule": "restricted", "allow": [{"type": "m.room_membership", "room_id": space_id}]},
            )
        topic = _ROOM_TOPICS.get(key)
        if topic:
            await synapse.set_room_state(room_id, "m.room.topic", {"topic": topic})
    LOGGER.info("Room state configuration applied")


async def _synapse_startup(app: FastAPI) -> None:
    """Background task: connect to Synapse, create bot and rooms."""
    if not await _wait_for_synapse(SYNAPSE_URL):
        return

    manifest = get_manifest()
    deployment = str(manifest.get("deployment", "pvarki"))
    domain = get_server_domain()

    synapse = SynapseAdmin(SYNAPSE_URL, domain)

    if not await _acquire_bot_token(synapse):
        await synapse.close()
        return

    app.state.synapse = synapse

    try:
        await _ensure_rooms(synapse, app, deployment, domain)
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Room setup failed: %s", exc)

    rooms = getattr(app.state, "rooms", None)
    if rooms:
        try:
            await _configure_rooms_state(synapse, rooms, deployment)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Room configuration failed: %s", exc)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start Synapse integration as a non-blocking background task."""
    task = asyncio.create_task(_synapse_startup(app))
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        synapse: Optional[SynapseAdmin] = getattr(app.state, "synapse", None)
        if synapse:
            await synapse.close()


def get_app() -> FastAPI:
    """Returns the FastAPI application."""
    init_logging(LOG_LEVEL)
    manifest = get_manifest()
    rm_base = manifest["rasenmaeher"]["init"]["base_uri"]
    deployment_domain_regex = rm_base.replace(".", r"\.").replace("https://", r"https://(.*\.)?")
    LOGGER.info("deployment_domain_regex={}".format(deployment_domain_regex))

    app = FastAPI(
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=app_lifespan,
        version=__version__,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=deployment_domain_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router=all_routers, prefix="/api/v1")
    app.include_router(router=all_routers_v2, prefix="/api/v2")

    LOGGER.info("API init done, setting log verbosity to '{}'.".format(logging.getLevelName(LOG_LEVEL)))

    return app
