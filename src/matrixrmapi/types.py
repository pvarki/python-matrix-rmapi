"""Shared domain types and constants."""

from enum import Enum
from typing import Dict


class AdminAction(Enum):
    """Possible admin-level actions that can be applied to a user."""

    PROMOTE = "promote"
    DEMOTE = "demote"


# Call-related event types that regular users (power level 0) must be allowed to send.
# Covers both legacy 1:1 calls and MSC3401 group calls (Element Call).
CALL_EVENTS_DEFAULT_LEVEL: Dict[str, int] = {
    "m.call.invite": 0,
    "m.call.answer": 0,
    "m.call.hangup": 0,
    "m.call.candidates": 0,
    "m.call.negotiate": 0,
    "m.call.reject": 0,
    "m.call.select_answer": 0,
    "org.matrix.msc3401.call": 0,
    "org.matrix.msc3401.call.member": 0,
}
