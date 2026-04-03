"""User lifecycle actions"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.generic import OperationResultResponse
from libpvarki.schemas.product import UserCRUDRequest

from ..config import get_manifest, get_server_domain
from ..synapseutils.synapse_admin import SynapseAdmin, matrix_user_id

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


def comes_from_rm(request: Request) -> None:
    """Check mTLS CN — raises 403 if not from Rasenmaeher."""
    payload = request.state.mtlsdn
    manifest = get_manifest()
    if payload.get("CN") != manifest["rasenmaeher"]["certcn"]:
        raise HTTPException(status_code=403)


def _synapse(request: Request) -> Optional[SynapseAdmin]:
    """Return SynapseAdmin from app state, or None if not yet ready."""
    val: Optional[SynapseAdmin] = getattr(request.app.state, "synapse", None)
    return val


def _rooms(request: Request) -> Optional[Dict[str, str]]:
    """Return room IDs dict from app state, or None if not yet ready."""
    val: Optional[Dict[str, str]] = getattr(request.app.state, "rooms", None)
    return val


def _public_room_ids(rooms: Dict[str, str]) -> list[str]:
    """Room IDs for the space + the three public rooms (not admin channel)."""
    return [rooms[k] for k in ("space", "general", "helpdesk", "offtopic") if k in rooms]


@router.post("/created")
async def user_created(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """New device cert created — force-join user to space and public rooms."""
    comes_from_rm(request)
    synapse = _synapse(request)
    rooms = _rooms(request)
    if synapse is None or rooms is None:
        LOGGER.warning("Synapse not ready; skipping room joins for %s (auto_join_rooms will handle it)", user.callsign)
        return OperationResultResponse(success=True)
    try:
        uid = matrix_user_id(user.callsign, get_server_domain())
    except ValueError as exc:
        LOGGER.error("Invalid callsign for Matrix: %s", exc)
        return OperationResultResponse(success=False)
    for room_id in _public_room_ids(rooms):
        await synapse.force_join(room_id, uid)
    LOGGER.info("Force-joined %s to public rooms", uid)
    return OperationResultResponse(success=True)


@router.post("/revoked")
async def user_revoked(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """Device cert revoked — deactivate and erase user from Synapse."""
    comes_from_rm(request)
    synapse = _synapse(request)
    if synapse is None:
        LOGGER.warning("Synapse not ready; cannot deactivate %s", user.callsign)
        return OperationResultResponse(success=True)
    try:
        uid = matrix_user_id(user.callsign, get_server_domain())
    except ValueError as exc:
        LOGGER.error("Invalid callsign for Matrix: %s", exc)
        return OperationResultResponse(success=False)
    try:
        await synapse.deactivate(uid)
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Failed to deactivate %s in Synapse: %s", uid, exc)
        return OperationResultResponse(success=False)
    LOGGER.info("Deactivated and erased %s from Synapse", uid)
    return OperationResultResponse(success=True)


async def _apply_admin_action(request: Request, uid: str, action: str) -> OperationResultResponse:
    """Promote or demote *uid*; queue if Synapse is not yet ready.

    *action* must be ``"promote"`` or ``"demote"``.
    """
    synapse = _synapse(request)
    rooms = _rooms(request)
    if synapse is None or rooms is None:
        request.app.state.pending_promotions[uid] = action
        LOGGER.info("Queued deferred %s for %s (Synapse not ready yet)", action, uid)
        return OperationResultResponse(success=True)
    try:
        level = 100 if action == "promote" else 0
        await synapse.set_power_level_in_rooms(_public_room_ids(rooms), uid, level)
        admin_id = rooms.get("admin")
        if admin_id:
            if action == "promote":
                await synapse.force_join(admin_id, uid)
            else:
                await synapse.kick(admin_id, uid)
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Failed to %s %s: %s", action, uid, exc)
        return OperationResultResponse(success=False)
    LOGGER.info("%sd %s (power level %d)", action.capitalize(), uid, level)
    return OperationResultResponse(success=True)


@router.post("/promoted")
async def user_promoted(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """User promoted to admin — power level 100 in public rooms, invite to admin channel."""
    comes_from_rm(request)
    try:
        uid = matrix_user_id(user.callsign, get_server_domain())
    except ValueError as exc:
        LOGGER.error("Invalid callsign for Matrix: %s", exc)
        return OperationResultResponse(success=False)
    return await _apply_admin_action(request, uid, "promote")


@router.post("/demoted")
async def user_demoted(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """User demoted from admin — remove power level 100, kick from admin channel."""
    comes_from_rm(request)
    try:
        uid = matrix_user_id(user.callsign, get_server_domain())
    except ValueError as exc:
        LOGGER.error("Invalid callsign for Matrix: %s", exc)
        return OperationResultResponse(success=False)
    return await _apply_admin_action(request, uid, "demote")


@router.put("/updated")
async def user_updated(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """Callsign updated — no-op (callsign change requires a new Matrix account)."""
    comes_from_rm(request)
    _ = user
    return OperationResultResponse(success=True)
