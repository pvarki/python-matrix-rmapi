"""MAS (Matrix Authentication Service) admin API helper"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import httpx

LOGGER = logging.getLogger(__name__)

ADMIN_SCOPE = "urn:mas:admin"
BOT_DEVICE_ID = "MATRIXRMAPIBOT"
BOT_TOKEN_SCOPE = (
    "urn:matrix:org.matrix.msc2967.client:api:* "
    "urn:synapse:admin:* "
    f"urn:matrix:org.matrix.msc2967.client:device:{BOT_DEVICE_ID}"
)
# Re-fetch the client-credentials token this many seconds before it expires
TOKEN_EXPIRY_SKEW = 30.0
# Lifetime of the bot personal session; a new one is created in memory when it runs out
BOT_TOKEN_EXPIRES_IN = 3600


class MasAdmin:
    """Async wrapper for the MAS admin API.

    Authenticates with OAuth2 client credentials (``urn:mas:admin`` scope);
    the short-lived admin token is cached and refreshed on demand.
    Call close() when done (or use as an async context manager).
    """

    def __init__(self, mas_url: str, client_id: str, client_secret: str) -> None:
        self._url = mas_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: Optional[str] = None
        self._token_expires: float = 0.0
        self._client: httpx.AsyncClient = httpx.AsyncClient()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "MasAdmin":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def _ensure_admin_token(self) -> str:
        """Return a cached admin token, fetching a fresh one when missing or stale."""
        if self._token and time.monotonic() < self._token_expires:
            return self._token
        resp = await self._client.post(
            f"{self._url}/oauth2/token",
            auth=(self._client_id, self._client_secret),
            data={"grant_type": "client_credentials", "scope": ADMIN_SCOPE},
            timeout=10.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = str(payload["access_token"])
        self._token_expires = (
            time.monotonic() + float(payload.get("expires_in", 300)) - TOKEN_EXPIRY_SKEW
        )
        return self._token

    async def _auth(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {await self._ensure_admin_token()}"}

    async def user_ulid_by_username(self, localpart: str) -> Optional[str]:
        """Return the MAS user ULID for localpart, or None if not found."""
        encoded = quote(localpart, safe="")
        resp = await self._client.get(
            f"{self._url}/api/admin/v1/users/by-username/{encoded}",
            headers=await self._auth(),
            timeout=10.0,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return str(resp.json()["data"]["id"])

    async def ensure_user(self, localpart: str) -> str:
        """Return the user's ULID, creating the user if needed.

        MAS provisions the user on the homeserver synchronously.
        """
        existing = await self.user_ulid_by_username(localpart)
        if existing:
            return existing
        resp = await self._client.post(
            f"{self._url}/api/admin/v1/users",
            headers=await self._auth(),
            json={"username": localpart},
            timeout=30.0,
        )
        resp.raise_for_status()
        ulid = str(resp.json()["data"]["id"])
        LOGGER.info("Created MAS user %s (%s)", localpart, ulid)
        return ulid

    async def create_bot_token(
        self,
        user_ulid: str,
        human_name: str,
        device_id: str = BOT_DEVICE_ID,
        expires_in: int = BOT_TOKEN_EXPIRES_IN,
    ) -> Tuple[str, float]:
        """Create an expiring personal session token for the bot user.

        Returns (access_token, expires_in seconds).
        """
        scope = (
            "urn:matrix:org.matrix.msc2967.client:api:* "
            "urn:synapse:admin:* "
            f"urn:matrix:org.matrix.msc2967.client:device:{device_id}"
        )
        resp = await self._client.post(
            f"{self._url}/api/admin/v1/personal-sessions",
            headers=await self._auth(),
            json={
                "actor_user_id": user_ulid,
                "human_name": human_name,
                "scope": scope,
                "expires_in": expires_in,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        attrs = resp.json()["data"]["attributes"]
        return str(attrs["access_token"]), float(attrs.get("expires_in", expires_in))

    async def deactivate_user(self, localpart: str) -> bool:
        """Deactivate user in MAS (erases them from the homeserver too).

        Returns True if the user was deactivated, False if they do not exist
        in MAS (never logged in).  Raises httpx.HTTPError on real failures.
        """
        ulid = await self.user_ulid_by_username(localpart)
        if ulid is None:
            return False
        resp = await self._client.post(
            f"{self._url}/api/admin/v1/users/{ulid}/deactivate",
            headers=await self._auth(),
            json={},
            timeout=30.0,
        )
        resp.raise_for_status()
        LOGGER.info("Deactivated MAS user %s (%s)", localpart, ulid)
        return True
