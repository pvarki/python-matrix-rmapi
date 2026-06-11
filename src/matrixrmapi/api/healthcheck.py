"""Health-check endpooint(s)"""

import logging

import httpx
from fastapi import APIRouter, Request
from libpvarki.schemas.product import ProductHealthCheckResponse

from ..config import MAS_HEALTH_URL, SYNAPSE_URL

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def request_healthcheck(request: Request) -> ProductHealthCheckResponse:
    """Check that the Matrix integration is initialised and Synapse and MAS respond"""
    if getattr(request.app.state, "synapse", None) is None or not getattr(
        request.app.state, "rooms", None
    ):
        return ProductHealthCheckResponse(
            healthy=False, extra="Matrix integration not initialised"
        )
    async with httpx.AsyncClient() as client:
        for name, url in (("Synapse", SYNAPSE_URL), ("MAS", MAS_HEALTH_URL)):
            try:
                resp = await client.get(f"{url}/health", timeout=2.0)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                LOGGER.warning("%s health check failed: %s", name, exc)
                return ProductHealthCheckResponse(
                    healthy=False, extra=f"{name} health check failed"
                )
    return ProductHealthCheckResponse(healthy=True)
