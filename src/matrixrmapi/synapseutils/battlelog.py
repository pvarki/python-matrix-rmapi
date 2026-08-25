"""The BattleLog ingest bot: a plain local user BattleLog reads room timelines with."""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

from .. import config
from .synapse_admin import SynapseAdmin

LOGGER = logging.getLogger(__name__)


async def acquire_bot_token(synapse: SynapseAdmin, user_id: str) -> str:
    """Return a usable access token for *user_id*, reusing the cached one when valid.

    Same contract as SynapseAdmin.setup() uses for the admin bot: read the file,
    validate it, mint a new one only when there is nothing usable. Minting is
    cheap but every mint leaves the previous token live, so do not do it per boot.
    """
    if config.BATTLELOG_TOKEN_FILE.exists():
        candidate = config.BATTLELOG_TOKEN_FILE.read_text(encoding="utf-8").strip()
        if candidate and await synapse.validate_user_token(candidate):
            LOGGER.info("Reused BattleLog bot token from %s", config.BATTLELOG_TOKEN_FILE)
            return candidate
        LOGGER.warning("Stored BattleLog bot token invalid, minting a new one")

    token = await synapse.mint_access_token(user_id)
    config.BATTLELOG_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.BATTLELOG_TOKEN_FILE.write_text(token, encoding="utf-8")
    os.chmod(config.BATTLELOG_TOKEN_FILE, 0o600)
    LOGGER.info("BattleLog bot token minted; saved to %s", config.BATTLELOG_TOKEN_FILE)
    return token


async def ensure_battlelog_bot(
    synapse: SynapseAdmin, rooms: Dict[str, str]
) -> Optional[str]:
    """Ensure the ingest bot exists, is joined everywhere, and return its token.

    "Everywhere" is the space, every standard room, and every child of the space,
    so rooms users created themselves are covered too without anyone inviting the
    bot by hand. Returns None if the bot could not be set up at all; individual
    room joins that fail are logged and skipped, because one invite-only room
    must not cost us all the others.

    Note this only gets the bot *into* the rooms. The standard rooms are
    end-to-end encrypted, so BattleLog will see ciphertext there until it grows a
    crypto-capable client, and it says so per room rather than failing silently.
    """
    user_id = await synapse.ensure_user(
        config.BATTLELOG_BOT_USERNAME, admin=False, displayname="BattleLog ingest"
    )
    # A /sync loop plus catch-up will hit 429 without this.
    await synapse.override_ratelimit(user_id)

    targets: List[str] = list(rooms.values())
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

    return await acquire_bot_token(synapse, user_id)
