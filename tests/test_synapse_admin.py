"""Unit tests for SynapseAdmin and matrix_user_id.

All HTTP calls are intercepted by patching the httpx.AsyncClient method on the
SynapseAdmin instance, so no real network is required.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from matrixrmapi.synapseutils.synapse_admin import SynapseAdmin, matrix_user_id

# httpx.Response needs a request object to call raise_for_status() cleanly.
_FAKE_REQUEST = httpx.Request("POST", "http://synapse.test/fake")


def _fake(status: int, body: Dict[str, Any]) -> httpx.Response:
    """Build a minimal fake httpx.Response."""
    return httpx.Response(status, json=body, request=_FAKE_REQUEST)


def _make_synapse() -> SynapseAdmin:
    """Return a SynapseAdmin ready for unit testing (real token + bot user set directly)."""
    sa = SynapseAdmin("http://synapse.test", "example.test")
    sa._token = "test-token"  # pylint: disable=protected-access
    sa._bot_user_id = "@bot:example.test"  # pylint: disable=protected-access
    return sa


# ---------------------------------------------------------------------------
# matrix_user_id
# ---------------------------------------------------------------------------


def test_matrix_user_id_lowercases_callsign() -> None:
    assert matrix_user_id("NORPPA11", "example.test") == "@norppa11:example.test"


def test_matrix_user_id_already_lowercase() -> None:
    assert matrix_user_id("norppa11", "example.test") == "@norppa11:example.test"


def test_matrix_user_id_with_dots_and_dashes() -> None:
    assert matrix_user_id("unit.11-a", "example.test") == "@unit.11-a:example.test"


def test_matrix_user_id_space_raises() -> None:
    with pytest.raises(ValueError):
        matrix_user_id("has space", "example.test")


def test_matrix_user_id_at_sign_raises() -> None:
    with pytest.raises(ValueError):
        matrix_user_id("bad@sign", "example.test")


def test_matrix_user_id_special_chars_raise() -> None:
    with pytest.raises(ValueError):
        matrix_user_id("excl!ama", "example.test")


# ---------------------------------------------------------------------------
# force_join
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_force_join_success() -> None:
    """Happy path: 200 response is accepted without error."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {"room_id": "!r:example.test"})
        await sa.force_join("!r:example.test", "@user:example.test")
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_force_join_user_not_in_synapse_skips() -> None:
    """404 means user hasn't logged in yet — must silently skip."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(404, {"errcode": "M_NOT_FOUND"})
        await sa.force_join("!r:example.test", "@ghost:example.test")  # must not raise


@pytest.mark.asyncio
async def test_force_join_already_in_room_skips() -> None:
    """403 + already in the room — idempotent, must not raise."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(
            403, {"errcode": "M_FORBIDDEN", "error": "User is already in the room."}
        )
        await sa.force_join("!r:example.test", "@user:example.test")  # must not raise


@pytest.mark.asyncio
async def test_force_join_other_403_raises() -> None:
    """403 with an unrecognised reason must propagate as HTTPStatusError."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(
            403, {"errcode": "M_FORBIDDEN", "error": "You do not have permission."}
        )
        with pytest.raises(httpx.HTTPStatusError):
            await sa.force_join("!r:example.test", "@user:example.test")


# ---------------------------------------------------------------------------
# deactivate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deactivate_success() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {"id_server_unbind_result": "success"})
        await sa.deactivate("@user:example.test")
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_user_not_found_skips() -> None:
    """User never logged in to Matrix — 404 must silently succeed."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(404, {"errcode": "M_NOT_FOUND"})
        await sa.deactivate("@ghost:example.test")  # must not raise


@pytest.mark.asyncio
async def test_deactivate_calls_v1_endpoint() -> None:
    """Admin API endpoint must be the stable v1 path."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {})
        await sa.deactivate("@user:example.test")
        url: str = mock_post.call_args.args[0]
        assert "/_synapse/admin/v1/deactivate/" in url
        assert "v2" not in url


@pytest.mark.asyncio
async def test_deactivate_sends_erase_true() -> None:
    """Deactivation must request GDPR erase."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {})
        await sa.deactivate("@user:example.test")
        body: Dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert body.get("erase") is True


# ---------------------------------------------------------------------------
# kick
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kick_success() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {})
        await sa.kick("!r:example.test", "@user:example.test")
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_kick_not_in_room_skips() -> None:
    """403 + not in the room — user already left; must not raise."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(
            403, {"errcode": "M_FORBIDDEN", "error": "User is not in the room."}
        )
        await sa.kick("!r:example.test", "@user:example.test")  # must not raise


@pytest.mark.asyncio
async def test_kick_other_403_raises() -> None:
    """403 with an unrecognised reason must propagate."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(
            403, {"errcode": "M_FORBIDDEN", "error": "You do not have permission."}
        )
        with pytest.raises(httpx.HTTPStatusError):
            await sa.kick("!r:example.test", "@user:example.test")


# ---------------------------------------------------------------------------
# create_room
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_room_sets_bot_at_power_200() -> None:
    """Bot must start at power level 200 so it can demote users at 100."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {"room_id": "!new:example.test"})
        await sa.create_room("TestRoom", "#test-room:example.test")
        body: Dict[str, Any] = mock_post.call_args.kwargs["json"]
        users: Dict[str, int] = body.get("power_level_content_override", {}).get("users", {})
        assert users.get("@bot:example.test") == 200


@pytest.mark.asyncio
async def test_create_space_sets_creation_content() -> None:
    """Spaces need creation_content.type = m.space."""
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {"room_id": "!space:example.test"})
        await sa.create_room("MySpace", "#my-space:example.test", is_space=True)
        body: Dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert body.get("creation_content", {}).get("type") == "m.space"


@pytest.mark.asyncio
async def test_create_private_room_uses_private_preset() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {"room_id": "!priv:example.test"})
        await sa.create_room("Admin", "#admin:example.test", is_private=True)
        body: Dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert body.get("preset") == "private_chat"


# ---------------------------------------------------------------------------
# room_id_for_alias
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_room_id_for_alias_found() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = _fake(200, {"room_id": "!abc:example.test"})
        result = await sa.room_id_for_alias("#general:example.test")
        assert result == "!abc:example.test"


@pytest.mark.asyncio
async def test_room_id_for_alias_not_found_returns_none() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = _fake(404, {"errcode": "M_NOT_FOUND"})
        result = await sa.room_id_for_alias("#nonexistent:example.test")
        assert result is None


# ---------------------------------------------------------------------------
# add_child_to_space
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_child_to_space() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "put", new_callable=AsyncMock
    ) as mock_put:
        mock_put.return_value = _fake(200, {})
        await sa.add_child_to_space("!space:example.test", "!room:example.test")
        mock_put.assert_called_once()
        url: str = mock_put.call_args.args[0]
        assert "m.space.child" in url


# ---------------------------------------------------------------------------
# set_room_state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_room_state_without_state_key() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "put", new_callable=AsyncMock
    ) as mock_put:
        mock_put.return_value = _fake(200, {})
        await sa.set_room_state("!r:example.test", "m.room.name", {"name": "Test"})
        url: str = mock_put.call_args.args[0]
        assert "m.room.name" in url


@pytest.mark.asyncio
async def test_set_room_state_with_state_key() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "put", new_callable=AsyncMock
    ) as mock_put:
        mock_put.return_value = _fake(200, {})
        await sa.set_room_state(
            "!r:example.test", "m.space.child", {"via": ["example.test"]}, state_key="!child:example.test"
        )
        url: str = mock_put.call_args.args[0]
        assert "m.space.child" in url
        assert "%21child" in url  # state key is URL-encoded into the path


# ---------------------------------------------------------------------------
# get_power_levels / set_user_power_level
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_power_levels() -> None:
    sa = _make_synapse()
    power_state = {"users": {"@bot:example.test": 200}, "users_default": 0}
    with patch.object(  # pylint: disable=protected-access
        sa._client, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = _fake(200, power_state)
        result = await sa.get_power_levels("!r:example.test")
        assert result["users"]["@bot:example.test"] == 200


@pytest.mark.asyncio
async def test_set_user_power_level_nonzero() -> None:
    """Setting a non-zero level must PUT the updated power levels state."""
    sa = _make_synapse()
    initial = {"users": {}, "users_default": 0}
    with patch.object(  # pylint: disable=protected-access
        sa._client, "get", new_callable=AsyncMock
    ) as mock_get, patch.object(  # pylint: disable=protected-access
        sa._client, "put", new_callable=AsyncMock
    ) as mock_put:
        mock_get.return_value = _fake(200, initial)
        mock_put.return_value = _fake(200, {})
        await sa.set_user_power_level("!r:example.test", "@user:example.test", 100)
        body: Dict[str, Any] = mock_put.call_args.kwargs["json"]
        assert body["users"]["@user:example.test"] == 100


@pytest.mark.asyncio
async def test_set_user_power_level_zero_removes_user() -> None:
    """Setting level 0 must remove the user entry rather than writing 0."""
    sa = _make_synapse()
    initial = {"users": {"@user:example.test": 100}, "users_default": 0}
    with patch.object(  # pylint: disable=protected-access
        sa._client, "get", new_callable=AsyncMock
    ) as mock_get, patch.object(  # pylint: disable=protected-access
        sa._client, "put", new_callable=AsyncMock
    ) as mock_put:
        mock_get.return_value = _fake(200, initial)
        mock_put.return_value = _fake(200, {})
        await sa.set_user_power_level("!r:example.test", "@user:example.test", 0)
        body: Dict[str, Any] = mock_put.call_args.kwargs["json"]
        assert "@user:example.test" not in body["users"]


# ---------------------------------------------------------------------------
# invite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invite_success() -> None:
    sa = _make_synapse()
    with patch.object(  # pylint: disable=protected-access
        sa._client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = _fake(200, {})
        await sa.invite("!r:example.test", "@user:example.test")
        body: Dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert body["user_id"] == "@user:example.test"


# ---------------------------------------------------------------------------
# set_power_level_in_rooms (batch helper)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_power_level_in_rooms_calls_each_room() -> None:
    sa = _make_synapse()
    room_ids = ["!r1:example.test", "!r2:example.test", "!r3:example.test"]
    initial = {"users": {}, "users_default": 0}
    with patch.object(  # pylint: disable=protected-access
        sa._client, "get", new_callable=AsyncMock
    ) as mock_get, patch.object(  # pylint: disable=protected-access
        sa._client, "put", new_callable=AsyncMock
    ) as mock_put:
        mock_get.return_value = _fake(200, initial)
        mock_put.return_value = _fake(200, {})
        await sa.set_power_level_in_rooms(room_ids, "@user:example.test", 100)
        assert mock_get.call_count == 3
        assert mock_put.call_count == 3
