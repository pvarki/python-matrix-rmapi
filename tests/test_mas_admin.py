"""Unit tests for MasAdmin.

All HTTP calls are intercepted by patching the httpx.AsyncClient method on the
MasAdmin instance, so no real network is required.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI

from matrixrmapi.utils import startup
from matrixrmapi.utils.mas_admin import MasAdmin

# httpx.Response needs a request object to call raise_for_status() cleanly.
FAKE_REQUEST = httpx.Request("POST", "http://mas.test/fake")

BOT_ULID = "01TESTULID0000000000000000"


def _fake(status: int, body: dict[str, Any]) -> httpx.Response:
    """Build a minimal fake httpx.Response."""
    return httpx.Response(status, json=body, request=FAKE_REQUEST)


def _make_mas(*, with_token: bool = True) -> MasAdmin:
    """Return a MasAdmin ready for unit testing.

    With with_token=True the admin token is pre-seeded so tests can focus on
    the admin API call itself without mocking the token fetch.
    """
    mas = MasAdmin("http://mas.test", "clientid", "clientsecret")
    if with_token:
        mas._token = "mas_admin_token"  # nosec B105
        mas._token_expires = time.monotonic() + 1000
    return mas


# ---------------------------------------------------------------------------
# _ensure_admin_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_token_request_shape() -> None:
    """Token fetch must use basic auth and client_credentials with admin scope."""
    mas = _make_mas(with_token=False)
    with patch.object(mas._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _fake(200, {"access_token": "tok", "expires_in": 300})
        token = await mas._ensure_admin_token()
    assert token == "tok"  # nosec B105
    assert mock_post.call_args.kwargs["auth"] == ("clientid", "clientsecret")
    data: dict[str, str] = mock_post.call_args.kwargs["data"]
    assert data["grant_type"] == "client_credentials"
    assert data["scope"] == "urn:mas:admin"


@pytest.mark.asyncio
async def test_admin_token_cached() -> None:
    """A fresh token must be reused, not re-fetched on every call."""
    mas = _make_mas(with_token=False)
    with patch.object(mas._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _fake(200, {"access_token": "tok", "expires_in": 300})
        await mas._ensure_admin_token()
        await mas._ensure_admin_token()
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_admin_token_refetched_after_expiry() -> None:
    """A stale token must trigger a new token fetch."""
    mas = _make_mas()
    mas._token_expires = time.monotonic() - 1
    with patch.object(mas._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _fake(200, {"access_token": "tok2", "expires_in": 300})
        token = await mas._ensure_admin_token()
    assert token == "tok2"  # nosec B105
    mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# ensure_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_user_existing_skips_create() -> None:
    """Existing user: ULID returned from lookup, no create POST."""
    mas = _make_mas()
    client = mas._client
    with (
        patch.object(client, "get", new_callable=AsyncMock) as mock_get,
        patch.object(client, "post", new_callable=AsyncMock) as mock_post,
    ):
        mock_get.return_value = _fake(200, {"data": {"id": BOT_ULID}})
        ulid = await mas.ensure_user("bot")
    assert ulid == BOT_ULID
    mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_user_creates_on_404() -> None:
    """Unknown user: 404 lookup must be followed by a create POST."""
    mas = _make_mas()
    client = mas._client
    with (
        patch.object(client, "get", new_callable=AsyncMock) as mock_get,
        patch.object(client, "post", new_callable=AsyncMock) as mock_post,
    ):
        mock_get.return_value = _fake(404, {"errors": [{"title": "not found"}]})
        mock_post.return_value = _fake(201, {"data": {"id": BOT_ULID}})
        ulid = await mas.ensure_user("bot")
    assert ulid == BOT_ULID
    body: dict[str, Any] = mock_post.call_args.kwargs["json"]
    assert body == {"username": "bot"}


# ---------------------------------------------------------------------------
# create_bot_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_bot_token_scopes_and_expiry() -> None:
    """Personal session must carry all three scopes and an expiry."""
    mas = _make_mas()
    with patch.object(mas._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _fake(
            201,
            {
                "data": {
                    "attributes": {"access_token": "mpt_bot_token", "expires_in": 3600}
                }
            },
        )
        token, expires_in = await mas.create_bot_token(BOT_ULID, "matrixrmapi bot")
    assert token == "mpt_bot_token"  # nosec B105
    assert expires_in == 3600
    body: dict[str, Any] = mock_post.call_args.kwargs["json"]
    assert body["expires_in"] == 3600
    assert body["actor_user_id"] == BOT_ULID
    scope: str = body["scope"]
    assert "urn:matrix:org.matrix.msc2967.client:api:*" in scope
    assert "urn:synapse:admin:*" in scope
    assert "urn:matrix:org.matrix.msc2967.client:device:MATRIXRMAPIBOT" in scope


# ---------------------------------------------------------------------------
# deactivate_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deactivate_user_found() -> None:
    """Known user: deactivate POST hits the user's ULID endpoint."""
    mas = _make_mas()
    client = mas._client
    with (
        patch.object(client, "get", new_callable=AsyncMock) as mock_get,
        patch.object(client, "post", new_callable=AsyncMock) as mock_post,
    ):
        mock_get.return_value = _fake(200, {"data": {"id": BOT_ULID}})
        mock_post.return_value = _fake(200, {"data": {"id": BOT_ULID}})
        deactivated = await mas.deactivate_user("norppa11")
    assert deactivated is True
    url: str = mock_post.call_args.args[0]
    assert url.endswith(f"/api/admin/v1/users/{BOT_ULID}/deactivate")


@pytest.mark.asyncio
async def test_deactivate_user_not_found_skips() -> None:
    """Unknown user (never logged in): no deactivate call, no raise, returns False."""
    mas = _make_mas()
    client = mas._client
    with (
        patch.object(client, "get", new_callable=AsyncMock) as mock_get,
        patch.object(client, "post", new_callable=AsyncMock) as mock_post,
    ):
        mock_get.return_value = _fake(404, {"errors": [{"title": "not found"}]})
        deactivated = await mas.deactivate_user("ghost")  # must not raise
    assert deactivated is False
    mock_post.assert_not_called()


# ---------------------------------------------------------------------------
# setup_mas_admin
# ---------------------------------------------------------------------------


def test_setup_mas_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-provided client id and secret yield a MasAdmin bound to app state."""
    monkeypatch.setattr(startup, "MAS_ADMIN_CLIENT_ID", "cid")
    monkeypatch.setattr(startup, "MAS_ADMIN_CLIENT_SECRET", "csecret")
    app = FastAPI()
    mas = startup.setup_mas_admin(app)
    assert mas is not None
    assert app.state.mas is mas
    assert mas._client_id == "cid"


def test_setup_mas_admin_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset secret must return None instead of raising."""
    monkeypatch.setattr(startup, "MAS_ADMIN_CLIENT_ID", "cid")
    monkeypatch.setattr(startup, "MAS_ADMIN_CLIENT_SECRET", "")
    app = FastAPI()
    assert startup.setup_mas_admin(app) is None
    assert getattr(app.state, "mas", None) is None


def test_setup_mas_admin_missing_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset client id must return None instead of raising."""
    monkeypatch.setattr(startup, "MAS_ADMIN_CLIENT_ID", "")
    monkeypatch.setattr(startup, "MAS_ADMIN_CLIENT_SECRET", "csecret")
    app = FastAPI()
    assert startup.setup_mas_admin(app) is None
    assert getattr(app.state, "mas", None) is None
