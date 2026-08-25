"""Routes for interoperation between products"""

from __future__ import annotations

import json
import logging
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.generic import OperationResultResponse

from .. import config
from ..schema.interop import ProductAddRequest, ProductAuthzResponse
from .usercrud import comes_from_rm

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


def _registered_products() -> List[str]:
    """Cert CNs RASENMAEHER has granted interop with us."""
    if not config.INTEROP_PRODUCTS_FILE.exists():
        return []
    try:
        data = json.loads(config.INTEROP_PRODUCTS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Could not read %s: %s", config.INTEROP_PRODUCTS_FILE, exc)
        return []
    return [str(item) for item in data]


def _register_product(certcn: str) -> None:
    """Add *certcn* to the registry. Idempotent."""
    products = _registered_products()
    if certcn in products:
        LOGGER.info("Product %s already registered", certcn)
        return
    products.append(certcn)
    config.INTEROP_PRODUCTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.INTEROP_PRODUCTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(products), encoding="utf-8")
    os.replace(tmp, config.INTEROP_PRODUCTS_FILE)
    LOGGER.info("Registered product %s for interop", certcn)


@router.post("/add")
async def add_product(
    product: ProductAddRequest, request: Request
) -> OperationResultResponse:
    """Product needs interop privileges. This can only be called by RASENMAEHER"""
    comes_from_rm(request)
    # We do not need the peer's cert itself, mTLS is terminated by nginx and the CN
    # it verified is what /authz checks. Accepting the field keeps the shared
    # ProductAddRequest contract.
    _register_product(product.certcn)
    return OperationResultResponse(success=True)


@router.get("/authz")
async def get_authz(request: Request) -> ProductAuthzResponse:
    """Hand a registered peer product the ingest bot's access token.

    The token belongs to a plain local user, not a server admin, so it can only
    read and write the rooms the bot has been joined to.
    """
    certcn = request.state.mtlsdn.get("CN")
    if certcn not in _registered_products():
        LOGGER.warning("Unregistered product %s asked for authz", certcn)
        raise HTTPException(status_code=403)
    if not config.BATTLELOG_TOKEN_FILE.exists():
        # Synapse startup has not got far enough yet, or it failed. Retryable.
        LOGGER.warning("No ingest bot token yet, %s must retry", certcn)
        raise HTTPException(status_code=503, detail="Ingest bot not ready")
    token = config.BATTLELOG_TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ProductAuthzResponse(type="bearer-token", token=token)
