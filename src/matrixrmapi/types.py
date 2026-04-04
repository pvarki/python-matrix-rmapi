"""Shared domain types."""

from enum import Enum


class AdminAction(Enum):
    """Possible admin-level actions that can be applied to a user."""

    PROMOTE = "promote"
    DEMOTE = "demote"
