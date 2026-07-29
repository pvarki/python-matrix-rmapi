"""Instructions endpoints"""

import logging

from fastapi import APIRouter, Depends
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.product import UserCRUDRequest

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


@router.post("/{language}")
async def user_intructions(user: UserCRUDRequest) -> dict[str, str]:
    """return user instructions"""
    return {
        "callsign": user.callsign,
        "instructions": "FIXME: Return something sane",
        "language": "en",
    }
