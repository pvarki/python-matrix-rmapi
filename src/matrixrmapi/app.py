"""Factory for the FastAPI app"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from libpvarki.logging import init_logging

from matrixrmapi import __version__
from .config import LOG_LEVEL, get_manifest
from .api import all_routers, all_routers_v2
from .synapseutils.synapse_admin import SynapseAdmin
from .synapseutils.startup import synapse_startup

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start Synapse integration as a non-blocking background task."""
    task = asyncio.create_task(synapse_startup(app))
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        synapse: Optional[SynapseAdmin] = getattr(app.state, "synapse", None)
        if synapse:
            await synapse.close()


def get_app() -> FastAPI:
    """Returns the FastAPI application."""
    init_logging(LOG_LEVEL)
    manifest = get_manifest()
    rm_base = manifest["rasenmaeher"]["init"]["base_uri"]
    deployment_domain_regex = rm_base.replace(".", r"\.").replace("https://", r"https://(.*\.)?")
    LOGGER.debug("deployment_domain_regex=%s", deployment_domain_regex)

    app = FastAPI(
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=app_lifespan,
        version=__version__,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=deployment_domain_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router=all_routers, prefix="/api/v1")
    app.include_router(router=all_routers_v2, prefix="/api/v2")
    app.state.pending_promotions = {}  # Dict[str, AdminAction]

    LOGGER.info("API init done, setting log verbosity to '%s'.", logging.getLevelName(LOG_LEVEL))

    return app
