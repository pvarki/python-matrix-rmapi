"""Health-check endpooint(s)"""

import logging

from fastapi import APIRouter, Depends
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.product import ProductHealthCheckResponse


LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


@router.get("")
async def request_healthcheck() -> ProductHealthCheckResponse:
    """Check that we are healthy, return accordingly"""
    return ProductHealthCheckResponse(healthy=True, extra="Dummy, nothing actually checked")
