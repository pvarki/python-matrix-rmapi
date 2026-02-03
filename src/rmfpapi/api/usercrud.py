""" "User actions"""

import logging

from fastapi import APIRouter, Depends, Request, HTTPException
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.product import UserCRUDRequest
from libpvarki.schemas.generic import OperationResultResponse

from ..config import get_manifest

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


def comes_from_rm(request: Request) -> None:
    """Check the CN, raises 403 if not"""
    payload = request.state.mtlsdn
    manifest = get_manifest()
    if payload.get("CN") != manifest["rasenmaeher"]["certcn"]:
        raise HTTPException(status_code=403)


@router.post("/created")
async def user_created(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """New device cert was created"""
    comes_from_rm(request)
    _ = user  # TODO: should we validate the cert at this point ??
    result = OperationResultResponse(success=True)
    return result


# While delete would be semantically better it takes no body and definitely forces the
# integration layer to keep track of UUIDs
@router.post("/revoked")
async def user_revoked(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """Device cert was revoked"""
    comes_from_rm(request)
    _ = user
    result = OperationResultResponse(success=True)
    return result


@router.post("/promoted")
async def user_promoted(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """Device cert was promoted to admin privileges"""
    comes_from_rm(request)
    _ = user
    result = OperationResultResponse(success=True)
    return result


@router.post("/demoted")
async def user_demoted(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """Device cert was demoted to standard privileges"""
    comes_from_rm(request)
    _ = user
    result = OperationResultResponse(success=True)
    return result


@router.put("/updated")
async def user_updated(
    user: UserCRUDRequest,
    request: Request,
) -> OperationResultResponse:
    """Device callsign updated"""
    comes_from_rm(request)
    _ = user
    result = OperationResultResponse(success=True)
    return result
