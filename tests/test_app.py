"""Unit tests for app-level helper functions in matrixrmapi.app."""

from __future__ import annotations

from typing import Dict, cast
from unittest.mock import AsyncMock

import pytest

from matrixrmapi.app import _apply_pending, _ensure_room
from matrixrmapi.synapseutils.synapse_admin import SynapseAdmin

_ROOMS: Dict[str, str] = {
    "space": "!space:x",
    "admin": "!admin:x",
    "general": "!general:x",
    "helpdesk": "!helpdesk:x",
    "offtopic": "!offtopic:x",
}

_PUBLIC_IDS = ["!space:x", "!general:x", "!helpdesk:x", "!offtopic:x"]


def _mock_synapse() -> AsyncMock:
    """AsyncMock shaped like SynapseAdmin; cast to SynapseAdmin at call sites."""
    return AsyncMock(spec=SynapseAdmin)


# ---------------------------------------------------------------------------
# _apply_pending
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_pending_promote_sets_power_and_joins_admin() -> None:
    """promote: power level 100 in public rooms, force-join admin channel."""
    synapse = _mock_synapse()
    await _apply_pending(cast(SynapseAdmin, synapse), _ROOMS, {"@user:x": "promote"})

    synapse.set_power_level_in_rooms.assert_called_once_with(_PUBLIC_IDS, "@user:x", 100)
    synapse.force_join.assert_called_once_with("!admin:x", "@user:x")


@pytest.mark.asyncio
async def test_apply_pending_demote_sets_power_and_kicks_admin() -> None:
    """demote: power level 0 in public rooms, kick from admin channel."""
    synapse = _mock_synapse()
    await _apply_pending(cast(SynapseAdmin, synapse), _ROOMS, {"@user:x": "demote"})

    synapse.set_power_level_in_rooms.assert_called_once_with(_PUBLIC_IDS, "@user:x", 0)
    synapse.kick.assert_called_once_with("!admin:x", "@user:x")


@pytest.mark.asyncio
async def test_apply_pending_multiple_users() -> None:
    """All queued users are processed."""
    synapse = _mock_synapse()
    await _apply_pending(
        cast(SynapseAdmin, synapse),
        _ROOMS,
        {"@alice:x": "promote", "@bob:x": "demote"},
    )

    assert synapse.set_power_level_in_rooms.call_count == 2
    synapse.set_power_level_in_rooms.assert_any_call(_PUBLIC_IDS, "@alice:x", 100)
    synapse.set_power_level_in_rooms.assert_any_call(_PUBLIC_IDS, "@bob:x", 0)


@pytest.mark.asyncio
async def test_apply_pending_no_admin_room_skips_join() -> None:
    """If admin room is missing from rooms dict, no force_join/kick is attempted."""
    synapse = _mock_synapse()
    rooms_no_admin = {k: v for k, v in _ROOMS.items() if k != "admin"}
    await _apply_pending(cast(SynapseAdmin, synapse), rooms_no_admin, {"@user:x": "promote"})

    synapse.force_join.assert_not_called()


@pytest.mark.asyncio
async def test_apply_pending_error_is_caught_not_raised() -> None:
    """A failure for one user must not propagate — subsequent users still run."""
    synapse = _mock_synapse()
    # Make first call raise, second call succeed
    synapse.set_power_level_in_rooms.side_effect = [
        RuntimeError("transient failure"),
        None,
    ]
    # Should not raise even though first user fails
    await _apply_pending(
        cast(SynapseAdmin, synapse),
        _ROOMS,
        {"@alice:x": "promote", "@bob:x": "promote"},
    )
    assert synapse.set_power_level_in_rooms.call_count == 2


@pytest.mark.asyncio
async def test_apply_pending_empty_queue_is_noop() -> None:
    """Empty pending dict must be a no-op — no Synapse calls made."""
    synapse = _mock_synapse()
    await _apply_pending(cast(SynapseAdmin, synapse), _ROOMS, {})
    synapse.set_power_level_in_rooms.assert_not_called()
    synapse.force_join.assert_not_called()
    synapse.kick.assert_not_called()


# ---------------------------------------------------------------------------
# _ensure_room
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_room_returns_existing_room() -> None:
    """If the alias already exists, no room is created."""
    synapse = _mock_synapse()
    synapse.room_id_for_alias.return_value = "!existing:example.test"
    result = await _ensure_room(cast(SynapseAdmin, synapse), "General", "#general:example.test", False, False)
    assert result == "!existing:example.test"
    synapse.create_room.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_room_creates_new_room() -> None:
    """If the alias is not found, the room is created."""
    synapse = _mock_synapse()
    synapse.room_id_for_alias.return_value = None
    synapse.create_room.return_value = "!new:example.test"
    result = await _ensure_room(cast(SynapseAdmin, synapse), "General", "#general:example.test", False, False)
    assert result == "!new:example.test"
    synapse.create_room.assert_called_once()
