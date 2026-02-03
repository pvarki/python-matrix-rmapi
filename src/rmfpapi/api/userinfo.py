"""Endpoints for information for the end-user"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.product import UserCRUDRequest

from ..config import get_manifest
from .usercrud import comes_from_rm

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


def get_callsign(request: Request) -> str:
    """extract callsign from metadata"""
    payload = request.state.mtlsdn
    return str(payload.get("CN"))


@router.post("/{language}/info.md", response_class=PlainTextResponse)
async def get_info(
    language: str,
    user: UserCRUDRequest,
    request: Request,
) -> str:
    """Return customized markdown"""
    comes_from_rm(request)
    callsign = user.callsign
    manifest = get_manifest()
    dname = manifest.get("deployment")
    if language == "fi":
        return f"""
## Feikkituote

Terve {callsign}! Tämä on esimerkki tuoteintegraatioiden kehittäjille.

Pyörii deploymentissa "{dname}"

        """
    # TODO: Add Swedish
    # Fall-back to english
    return f"""
## Fake product

Hello {callsign}! This is a minimal example integration for integration developers' reference.

Running on deployment "{dname}"
"""
