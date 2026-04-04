"""Synapse startup helpers: health-check, bot registration, room setup."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Tuple

import filelock
import httpx
from fastapi import FastAPI

from ..config import (
    SYNAPSE_BOT_USERNAME,
    SYNAPSE_REGISTRATION_SECRET,
    SYNAPSE_TOKEN_FILE,
    SYNAPSE_URL,
    get_manifest,
    get_server_domain,
)
from ..types import AdminAction
from .synapse_admin import SynapseAdmin

LOGGER = logging.getLogger(__name__)

# (key, alias_suffix, display_name, is_space, is_private)
ROOMS_CONFIG: List[Tuple[str, str, str, bool, bool]] = [
    ("space", "{d}-space", "{d}", True, False),
    ("admin", "{d}-admin", "Admin channel", False, True),
    ("general", "{d}-general", "98-General-for-all", False, False),
    ("helpdesk", "{d}-helpdesk", "99-Helpdesk", False, False),
    ("offtopic", "{d}-offtopic", "Off topic", False, False),
]

ROOM_TOPICS: Dict[str, str] = {
    "general": "Work discussion that does not fit any other room.",
    "helpdesk": "Report issues and get help from here.",
    "offtopic": "Everything that is not about the topics or work.",
}


async def wait_for_synapse(synapse_url: str, retries: int = 60, interval: float = 5.0) -> bool:
    """Poll Synapse /health until it responds 200. Returns True on success."""
    LOGGER.info("Waiting for Synapse at %s ...", synapse_url)
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
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


async def acquire_bot_token(synapse: SynapseAdmin) -> Tuple[bool, bool]:
    """Acquire the admin bot token using a file lock for worker coordination.

    Returns ``(success, is_init_worker)``.  Only the init worker should run
    room creation and configuration; follower workers merely load the token
    and then derive existing room IDs.
    """
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
        return True, True
    except filelock.Timeout:
        LOGGER.warning("Another worker is initialising the Synapse bot, waiting ...")
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Bot token acquisition failed: %s", exc)
        return False, False
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
        return False, False

    # Load and validate the token written by the init worker
    try:
        await synapse.setup("", SYNAPSE_BOT_USERNAME, SYNAPSE_TOKEN_FILE)
        return True, False
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Failed to load bot token from file: %s", exc)
        return False, False


async def ensure_room(synapse: SynapseAdmin, name: str, alias: str, is_space: bool, is_private: bool) -> str:
    """Return room_id for alias, creating the room if it does not exist."""
    existing = await synapse.room_id_for_alias(alias)
    if existing:
        LOGGER.info("Room %s already exists: %s", alias, existing)
        return existing
    room_id = await synapse.create_room(name, alias, is_space=is_space, is_private=is_private)
    LOGGER.info("Created room %s -> %s", alias, room_id)
    return room_id


async def ensure_rooms(synapse: SynapseAdmin, deployment: str, domain: str) -> Dict[str, str]:
    """Create space and rooms if they don't exist; return room IDs dict."""
    room_ids: Dict[str, str] = {}
    space_id: Optional[str] = None

    for key, alias_tpl, name_tpl, is_space, is_private in ROOMS_CONFIG:
        alias = f"#{alias_tpl.format(d=deployment)}:{domain}"
        room_ids[key] = await ensure_room(synapse, name_tpl.format(d=deployment), alias, is_space, is_private)
        if is_space:
            space_id = room_ids[key]

    if space_id:
        for key, room_id in room_ids.items():
            if key != "space":
                await synapse.add_child_to_space(space_id, room_id)

    return room_ids


async def apply_pending(synapse: SynapseAdmin, rooms: Dict[str, str], pending: Dict[str, AdminAction]) -> None:
    """Apply promotions/demotions that were queued while Synapse was still starting."""
    public_ids = [rooms[k] for k in ("space", "general", "helpdesk", "offtopic") if k in rooms]
    admin_id = rooms.get("admin")
    for uid, action in pending.items():
        try:
            if action is AdminAction.PROMOTE:
                await synapse.set_power_level_in_rooms(public_ids, uid, 100)
                if admin_id:
                    await synapse.force_join(admin_id, uid)
                LOGGER.info("Applied deferred promotion for %s", uid)
            elif action is AdminAction.DEMOTE:
                await synapse.set_power_level_in_rooms(public_ids, uid, 0)
                if admin_id:
                    await synapse.kick(admin_id, uid)
                LOGGER.info("Applied deferred demotion for %s", uid)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Failed to apply deferred %s for %s: %s", action.value, uid, exc)


async def configure_rooms_state(synapse: SynapseAdmin, rooms: Dict[str, str], deployment: str) -> None:
    """Apply join rules, encryption, history visibility, topics and names to all rooms.

    All state events are idempotent in Matrix — safe to re-apply on every restart.
    """
    name_by_key = {key: name_tpl.format(d=deployment) for key, _, name_tpl, _, _ in ROOMS_CONFIG}
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
        topic = ROOM_TOPICS.get(key)
        if topic:
            await synapse.set_room_state(room_id, "m.room.topic", {"topic": topic})
    LOGGER.info("Room state configuration applied")


async def synapse_startup(app: FastAPI) -> None:
    """Background task: connect to Synapse, create bot and rooms."""
    if not await wait_for_synapse(SYNAPSE_URL):
        return

    manifest = get_manifest()
    deployment = str(manifest.get("deployment", "pvarki"))
    domain = get_server_domain()

    synapse = SynapseAdmin(SYNAPSE_URL, domain)

    ok, is_init = await acquire_bot_token(synapse)
    if not ok:
        await synapse.close()
        return

    app.state.synapse = synapse

    try:
        room_ids = await ensure_rooms(synapse, deployment, domain)
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Room setup failed: %s", exc)
        return

    if is_init:
        # Only the init worker applies state configuration to avoid redundant
        # duplicate PUTs from every worker on every restart.
        try:
            await configure_rooms_state(synapse, room_ids, deployment)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Room configuration failed (rooms still usable): %s", exc)
    else:
        LOGGER.info("Follower worker: skipping room state configuration (handled by init worker)")

    # Expose rooms after configuration — prevents /promoted from racing with
    # configure_rooms_state's power-level read-modify-write on the space.
    # Set even if configuration partially failed: rooms exist and are usable.
    app.state.rooms = room_ids
    LOGGER.info("Synapse rooms ready: %s", room_ids)

    # Apply any promotions/demotions that arrived while rooms were not yet set.
    # Snapshot and clear atomically (no await between) so any new requests that
    # arrive during apply_pending go into the now-empty dict, not the snapshot.
    pending: Dict[str, AdminAction] = dict(app.state.pending_promotions)
    app.state.pending_promotions.clear()
    if pending:
        LOGGER.info("Processing %d deferred promotion(s)/demotion(s)", len(pending))
        await apply_pending(synapse, room_ids, pending)
