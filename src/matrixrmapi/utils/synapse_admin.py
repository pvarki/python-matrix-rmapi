"""Synapse admin API helper"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from ..types import CALL_EVENTS_DEFAULT_LEVEL
from .mas_admin import MasAdmin

LOGGER = logging.getLogger(__name__)

MATRIX_LOCALPART_RE = re.compile(r"^[a-z0-9._\-=/+]+$")
# Create a new bot session this many seconds before the old one expires
BOT_TOKEN_EXPIRY_SKEW = 60.0


def matrix_user_id(callsign: str, server_domain: str) -> str:
    """Build @localpart:domain from callsign. Raises ValueError for invalid callsigns."""
    localpart = callsign.lower()
    if not MATRIX_LOCALPART_RE.match(localpart):
        raise ValueError(
            f"Callsign {callsign!r} produces invalid Matrix localpart: {localpart!r}"
        )
    return f"@{localpart}:{server_domain}"


class SynapseAdmin:
    """Async wrapper for the Synapse admin API.

    Call setup() once before using any other methods.
    Call close() when done (or use as an async context manager).
    """

    def __init__(self, synapse_url: str, server_domain: str) -> None:
        self._url = synapse_url.rstrip("/")
        self._domain = server_domain
        self._token: Optional[str] = None
        self._token_expires: float = 0.0
        self._token_lock: asyncio.Lock = asyncio.Lock()
        self._mas: Optional[MasAdmin] = None
        self._bot_username: Optional[str] = None
        self._bot_ulid: Optional[str] = None
        self._bot_user_id: Optional[str] = None
        self._client: httpx.AsyncClient = httpx.AsyncClient()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "SynapseAdmin":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    async def setup(self, bot_username: str, mas: MasAdmin) -> None:
        """Ensure the bot user exists in MAS and create an in-memory session token."""
        self._bot_user_id = f"@{bot_username}:{self._domain}"
        self._bot_username = bot_username
        self._mas = mas
        self._bot_ulid = await mas.ensure_user(bot_username)
        await self._create_token()
        LOGGER.info("Bot session created via MAS")

        await self._exempt_bot_from_ratelimit(bot_username)

    async def _create_token(self) -> None:
        """Create a new bot session via MAS; recreates the bot user if it no longer exists."""
        if self._mas is None or self._bot_ulid is None:
            raise RuntimeError("SynapseAdmin.setup() has not been called")
        human_name = f"matrixrmapi bot ({self._domain})"
        try:
            token, expires_in = await self._mas.create_bot_token(
                self._bot_ulid, human_name
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404 or self._bot_username is None:
                raise
            # Bot user no longer exists in MAS (e.g. wiped database) -- re-create and retry once
            LOGGER.warning("Bot user %s not found in MAS, recreating", self._bot_ulid)
            self._bot_ulid = await self._mas.ensure_user(self._bot_username)
            token, expires_in = await self._mas.create_bot_token(
                self._bot_ulid, human_name
            )
        self._token = token
        self._token_expires = time.monotonic() + expires_in - BOT_TOKEN_EXPIRY_SKEW

    async def _exempt_bot_from_ratelimit(self, bot_username: str) -> None:
        """Remove rate-limit restrictions for the bot user so concurrent room setup never gets 429."""
        user_id = f"@{bot_username}:{self._domain}"
        encoded = quote(user_id, safe="")
        try:
            resp = await self._client.post(
                f"{self._url}/_synapse/admin/v1/users/{encoded}/override_ratelimit",
                headers=await self._auth(),
                json={"messages_per_second": 0, "burst_count": 0},
                timeout=10.0,
            )
            resp.raise_for_status()
            LOGGER.info("Rate-limit override applied for %s", user_id)
        except Exception as exc:
            LOGGER.warning("Failed to override rate limit for %s: %s", user_id, exc)

    async def _auth(self) -> Dict[str, str]:
        """Return the bearer header, creating a new session when missing or expired."""
        if not self._token:
            raise RuntimeError("SynapseAdmin.setup() has not been called")
        if time.monotonic() >= self._token_expires:
            async with self._token_lock:
                if time.monotonic() >= self._token_expires:
                    await self._create_token()
        return {"Authorization": f"Bearer {self._token}"}

    # ------------------------------------------------------------------
    # Room / space management
    # ------------------------------------------------------------------

    async def room_id_for_alias(self, alias: str) -> Optional[str]:
        """Return room_id for alias, or None if not found."""
        encoded = quote(alias, safe="")
        resp = await self._client.get(
            f"{self._url}/_matrix/client/v3/directory/room/{encoded}",
            headers=await self._auth(),
            timeout=10.0,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return str(resp.json()["room_id"])

    async def create_room(
        self,
        name: str,
        alias: str,
        *,
        is_space: bool = False,
        is_private: bool = False,
    ) -> str:
        """Create a room or space; return room_id."""
        local_part = alias.split(":")[0].lstrip("#")
        body: Dict[str, Any] = {
            "name": name,
            "room_alias_name": local_part,
            "preset": "private_chat" if is_private else "public_chat",
            "visibility": "private",
        }
        if is_space:
            body["creation_content"] = {"type": "m.space"}
        # Set bot to power level 200 so it can always demote admins (who are at 100).
        # Matrix spec: you cannot lower a user at power level >= your own.
        # Explicitly allow call events at level 0 so normal users can start calls.
        if self._bot_user_id:
            body["power_level_content_override"] = {
                "users": {self._bot_user_id: 200},
                "events": dict(CALL_EVENTS_DEFAULT_LEVEL),
            }

        resp = await self._client.post(
            f"{self._url}/_matrix/client/v3/createRoom",
            headers=await self._auth(),
            json=body,
            timeout=30.0,
        )
        resp.raise_for_status()
        return str(resp.json()["room_id"])

    async def add_child_to_space(self, space_id: str, room_id: str) -> None:
        """Register room as a child of space."""
        encoded_room = quote(room_id, safe="")
        resp = await self._client.put(
            f"{self._url}/_matrix/client/v3/rooms/{space_id}/state/m.space.child/{encoded_room}",
            headers=await self._auth(),
            json={"via": [self._domain], "suggested": False},
            timeout=10.0,
        )
        resp.raise_for_status()

    async def set_room_state(
        self,
        room_id: str,
        event_type: str,
        content: Dict[str, Any],
        state_key: str = "",
    ) -> None:
        """Send a room state event."""
        path = f"{self._url}/_matrix/client/v3/rooms/{room_id}/state/{event_type}"
        if state_key:
            path = f"{path}/{quote(state_key, safe='')}"
        resp = await self._client.put(
            path, headers=await self._auth(), json=content, timeout=10.0
        )
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    async def force_join(self, room_id: str, user_id: str) -> None:
        """Force-join user to room via admin API.

        Silently skips if the user does not exist in Synapse yet (404) —
        auto_join_rooms in homeserver.yaml will handle the initial join.
        """
        resp = await self._client.post(
            f"{self._url}/_synapse/admin/v1/join/{room_id}",
            headers=await self._auth(),
            json={"user_id": user_id},
            timeout=10.0,
        )
        if resp.status_code == 404:
            LOGGER.info(
                "User %s not in Synapse yet; skipping force_join (auto_join_rooms will handle it)",
                user_id,
            )
            return
        if resp.status_code == 403:
            body = resp.json()
            if body.get(
                "errcode"
            ) == "M_FORBIDDEN" and "already in the room" in body.get("error", ""):
                LOGGER.info(
                    "User %s is already in room %s; skipping force_join",
                    user_id,
                    room_id,
                )
                return
        resp.raise_for_status()

    async def get_power_levels(self, room_id: str) -> Dict[str, Any]:
        """Get the m.room.power_levels state for a room."""
        resp = await self._client.get(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels",
            headers=await self._auth(),
            timeout=10.0,
        )
        resp.raise_for_status()
        return dict(resp.json())

    async def set_user_power_level(
        self, room_id: str, user_id: str, level: int
    ) -> None:
        """Set a single user's power level in a room."""
        levels = await self.get_power_levels(room_id)
        users: Dict[str, int] = dict(levels.get("users", {}))
        if level == 0:
            users.pop(user_id, None)
        else:
            users[user_id] = level
        levels["users"] = users
        resp = await self._client.put(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels",
            headers=await self._auth(),
            json=levels,
            timeout=10.0,
        )
        resp.raise_for_status()

    async def invite(self, room_id: str, user_id: str) -> None:
        """Invite user to room."""
        resp = await self._client.post(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/invite",
            headers=await self._auth(),
            json={"user_id": user_id},
            timeout=10.0,
        )
        resp.raise_for_status()

    async def kick(self, room_id: str, user_id: str) -> None:
        """Kick user from room. Silently skips if user is not in the room."""
        resp = await self._client.post(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/kick",
            headers=await self._auth(),
            json={"user_id": user_id},
            timeout=10.0,
        )
        if resp.status_code == 403:
            body = resp.json()
            if body.get("errcode") == "M_FORBIDDEN" and "not in the room" in body.get(
                "error", ""
            ):
                LOGGER.info(
                    "User %s is not in room %s; skipping kick", user_id, room_id
                )
                return
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # Batch helpers used by usercrud
    # ------------------------------------------------------------------

    async def set_power_level_in_rooms(
        self, room_ids: List[str], user_id: str, level: int
    ) -> None:
        """Set power level for user across multiple rooms."""
        for room_id in room_ids:
            await self.set_user_power_level(room_id, user_id, level)
