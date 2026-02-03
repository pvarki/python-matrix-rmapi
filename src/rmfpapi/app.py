""" "factory for the fastpi app"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from libpvarki.logging import init_logging

from rmfpapi import __version__
from .config import LOG_LEVEL, get_manifest
from .api import all_routers, all_routers_v2

LOGGER = logging.getLogger(__name__)


def get_app() -> FastAPI:
    """Returns the FastAPI application."""
    init_logging(LOG_LEVEL)
    manifest = get_manifest()
    rm_base = manifest["rasenmaeher"]["init"]["base_uri"]
    deployment_domain_regex = rm_base.replace(".", r"\.").replace("https://", r"https://(.*\.)?")
    LOGGER.info("deployment_domain_regex={}".format(deployment_domain_regex))

    app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=deployment_domain_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router=all_routers, prefix="/api/v1")
    app.include_router(router=all_routers_v2, prefix="/api/v2")

    LOGGER.info("API init done, setting log verbosity to '{}'.".format(logging.getLevelName(LOG_LEVEL)))

    return app
