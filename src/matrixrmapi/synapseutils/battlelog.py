"""The BattleLog ingest bot: a local user BattleLog reads room timelines as."""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Optional

from .. import config
from .synapse_admin import SynapseAdmin

LOGGER = logging.getLogger(__name__)


def _stored() -> Optional[Dict[str, str]]:
    """Previously issued bot credentials, if we have any."""
    if not config.BATTLELOG_CREDENTIALS_FILE.exists():
        return None
    try:
        data = json.loads(config.BATTLELOG_CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Could not read %s: %s", config.BATTLELOG_CREDENTIALS_FILE, exc)
        return None
    if "user_id" in data and "access_token" in data:
        return {"user_id": str(data["user_id"]), "access_token": str(data["access_token"])}
    return None


def _store(user_id: str, access_token: str) -> None:
    config.BATTLELOG_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.BATTLELOG_CREDENTIALS_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"user_id": user_id, "access_token": access_token}), encoding="utf-8"
    )
    os.chmod(tmp, 0o600)
    os.replace(tmp, config.BATTLELOG_CREDENTIALS_FILE)


async def ensure_battlelog_bot(synapse: SynapseAdmin, rooms: Dict[str, str]) -> Optional[str]:
    """Ensure the ingest bot exists and is joined everywhere. Returns its MXID.

    The bot is created by **shared-secret registration**, not by the admin
    create-or-modify API, for one reason: registering creates a device and binds
    the returned token to it. Room keys in Matrix are shared with devices, so a
    device-less token — which is what the admin "login as user" API hands out —
    can be in every room and still decrypt nothing.

    The token is therefore stored and reused. Re-registering is neither possible
    (the account exists) nor desirable: a new device would not have the room keys
    already shared with the old one.

    "Everywhere" is the space, every standard room, and every child of the space,
    so rooms users created themselves are covered without anyone inviting the bot
    by hand. Individual joins that fail are logged and skipped, because one
    invite-only room must not cost us all the others.
    """
    existing = _stored()
    if existing and await synapse.validate_user_token(existing["access_token"]):
        user_id = existing["user_id"]
    else:
        if existing:
            LOGGER.warning("Stored BattleLog bot token is no longer valid, registering again")
        token = await synapse.register_bot(
            config.SYNAPSE_REGISTRATION_SECRET,
            config.BATTLELOG_BOT_USERNAME,
            admin=False,
        )
        user_id = f"@{config.BATTLELOG_BOT_USERNAME}:{synapse.domain}"
        _store(user_id, token)
        LOGGER.info("Registered BattleLog ingest bot %s with its own device", user_id)

    # A /sync loop plus catch-up will hit 429 without this.
    await synapse.override_ratelimit(user_id)

    targets = list(rooms.values())
    space_id = rooms.get("space")
    if space_id:
        for child in await synapse.space_children(space_id):
            if child not in targets:
                targets.append(child)

    joined = 0
    for room_id in targets:
        try:
            await synapse.force_join(room_id, user_id)
            joined += 1
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Could not join %s to %s: %s", user_id, room_id, exc)
    LOGGER.info("BattleLog bot %s joined to %d/%d rooms", user_id, joined, len(targets))
    return user_id
