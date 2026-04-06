"""Synapse admin API helper"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from ..types import CALL_EVENTS_DEFAULT_LEVEL

LOGGER = logging.getLogger(__name__)

MATRIX_LOCALPART_RE = re.compile(r"^[a-z0-9._\-=/+]+$")


def matrix_user_id(callsign: str, server_domain: str) -> str:
    """Build @localpart:domain from callsign. Raises ValueError for invalid callsigns."""
    localpart = callsign.lower()
    if not MATRIX_LOCALPART_RE.match(localpart):
        raise ValueError(f"Callsign {callsign!r} produces invalid Matrix localpart: {localpart!r}")
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

    async def setup(self, registration_secret: str, bot_username: str, token_file: Path) -> None:
        """Acquire admin token: load from file or register bot if missing/invalid."""
        self._bot_user_id = f"@{bot_username}:{self._domain}"
        if token_file.exists():
            candidate = token_file.read_text().strip()
            if await self._validate(candidate):
                self._token = candidate
                LOGGER.info("Reused bot token from %s", token_file)
                await self._exempt_bot_from_ratelimit(bot_username)
                return
            LOGGER.warning("Stored token invalid, will re-register bot")

        token = await self._register_bot(registration_secret, bot_username)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token)
        os.chmod(token_file, 0o600)
        self._token = token
        LOGGER.info("Bot registered; token saved to %s", token_file)

        await self._exempt_bot_from_ratelimit(bot_username)

    async def _exempt_bot_from_ratelimit(self, bot_username: str) -> None:
        """Remove rate-limit restrictions for the bot user so concurrent room setup never gets 429."""
        user_id = f"@{bot_username}:{self._domain}"
        encoded = quote(user_id, safe="")
        try:
            resp = await self._client.post(
                f"{self._url}/_synapse/admin/v1/users/{encoded}/override_ratelimit",
                headers=self._auth,
                json={"messages_per_second": 0, "burst_count": 0},
                timeout=10.0,
            )
            resp.raise_for_status()
            LOGGER.info("Rate-limit override applied for %s", user_id)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Failed to override rate limit for %s: %s", user_id, exc)

    async def _validate(self, token: str) -> bool:
        """Return True if token is accepted by the admin API."""
        try:
            resp = await self._client.get(
                f"{self._url}/_synapse/admin/v1/server_version",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            return resp.status_code == 200
        except Exception:  # pylint: disable=broad-except
            return False

    async def _register_bot(self, registration_secret: str, username: str) -> str:
        """Register a new Synapse admin user via HMAC-signed register endpoint."""
        nonce_resp = await self._client.get(
            f"{self._url}/_synapse/admin/v1/register",
            timeout=10.0,
        )
        nonce_resp.raise_for_status()
        nonce: str = nonce_resp.json()["nonce"]

        # Synapse uses HMAC-SHA1 for the registration MAC
        rand_password = secrets.token_hex(32)
        mac_content = f"{nonce}\0{username}\0{rand_password}\0admin"
        mac = hmac.new(
            registration_secret.encode("utf-8"),
            mac_content.encode("utf-8"),
            hashlib.sha1,  # nosec B324 - required by Synapse registration API
        ).hexdigest()

        reg_resp = await self._client.post(
            f"{self._url}/_synapse/admin/v1/register",
            json={
                "nonce": nonce,
                "username": username,
                "password": rand_password,
                "admin": True,
                "mac": mac,
            },
            timeout=30.0,
        )

        if reg_resp.status_code == 400 and reg_resp.json().get("errcode") == "M_USER_IN_USE":
            LOGGER.critical(
                "Bot user @%s:%s already exists but no valid token file was found. "
                "Manual recovery: deactivate the bot via Synapse admin UI, "
                "delete the token file, then restart matrixrmapi.",
                username,
                self._domain,
            )
            raise RuntimeError(f"Bot user already exists and cannot be recovered automatically: {username}")

        reg_resp.raise_for_status()
        return str(reg_resp.json()["access_token"])

    @property
    def _auth(self) -> Dict[str, str]:
        if not self._token:
            raise RuntimeError("SynapseAdmin.setup() has not been called")
        return {"Authorization": f"Bearer {self._token}"}

    # ------------------------------------------------------------------
    # Room / space management
    # ------------------------------------------------------------------

    async def room_id_for_alias(self, alias: str) -> Optional[str]:
        """Return room_id for alias, or None if not found."""
        encoded = quote(alias, safe="")
        resp = await self._client.get(
            f"{self._url}/_matrix/client/v3/directory/room/{encoded}",
            headers=self._auth,
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
            headers=self._auth,
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
            headers=self._auth,
            json={"via": [self._domain], "suggested": False},
            timeout=10.0,
        )
        resp.raise_for_status()

    async def set_room_state(self, room_id: str, event_type: str, content: Dict[str, Any], state_key: str = "") -> None:
        """Send a room state event."""
        path = f"{self._url}/_matrix/client/v3/rooms/{room_id}/state/{event_type}"
        if state_key:
            path = f"{path}/{quote(state_key, safe='')}"
        resp = await self._client.put(path, headers=self._auth, json=content, timeout=10.0)
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
            headers=self._auth,
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
            if body.get("errcode") == "M_FORBIDDEN" and "already in the room" in body.get("error", ""):
                LOGGER.info("User %s is already in room %s; skipping force_join", user_id, room_id)
                return
        resp.raise_for_status()

    async def deactivate(self, user_id: str) -> None:
        """Deactivate and erase user. Silently succeeds if user does not exist in Synapse."""
        # Use v1 endpoint — v2 path (/v2/users/{id}/deactivate) is unrecognised in some
        # Synapse versions; v1 has been stable since early Synapse releases.
        resp = await self._client.post(
            f"{self._url}/_synapse/admin/v1/deactivate/{quote(user_id, safe='')}",
            headers=self._auth,
            json={"erase": True},
            timeout=30.0,
        )
        if resp.status_code == 404:
            LOGGER.info("User %s not found in Synapse; nothing to deactivate", user_id)
            return
        resp.raise_for_status()

    async def get_power_levels(self, room_id: str) -> Dict[str, Any]:
        """Get the m.room.power_levels state for a room."""
        resp = await self._client.get(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels",
            headers=self._auth,
            timeout=10.0,
        )
        resp.raise_for_status()
        return dict(resp.json())

    async def set_user_power_level(self, room_id: str, user_id: str, level: int) -> None:
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
            headers=self._auth,
            json=levels,
            timeout=10.0,
        )
        resp.raise_for_status()

    async def invite(self, room_id: str, user_id: str) -> None:
        """Invite user to room."""
        resp = await self._client.post(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/invite",
            headers=self._auth,
            json={"user_id": user_id},
            timeout=10.0,
        )
        resp.raise_for_status()

    async def kick(self, room_id: str, user_id: str) -> None:
        """Kick user from room. Silently skips if user is not in the room."""
        resp = await self._client.post(
            f"{self._url}/_matrix/client/v3/rooms/{room_id}/kick",
            headers=self._auth,
            json={"user_id": user_id},
            timeout=10.0,
        )
        if resp.status_code == 403:
            body = resp.json()
            if body.get("errcode") == "M_FORBIDDEN" and "not in the room" in body.get("error", ""):
                LOGGER.info("User %s is not in room %s; skipping kick", user_id, room_id)
                return
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # Batch helpers used by usercrud
    # ------------------------------------------------------------------

    async def set_power_level_in_rooms(self, room_ids: List[str], user_id: str, level: int) -> None:
        """Set power level for user across multiple rooms."""
        for room_id in room_ids:
            await self.set_user_power_level(room_id, user_id, level)
