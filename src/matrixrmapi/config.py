"""Configurations with .env support"""

import functools
import json
import logging
from pathlib import Path
from typing import Any, cast

from starlette.config import Config

LOGGER = logging.getLogger(__name__)

cfg = Config()  # not supporting .env files anymore because https://github.com/encode/starlette/discussions/2446

LOG_LEVEL: int = cfg("LOG_LEVEL", default=20, cast=int)
TEMPLATES_PATH: Path = cfg(
    "TEMPLATES_PATH", cast=Path, default=Path(__file__).parent / "templates"
)

SYNAPSE_URL: str = cfg("SYNAPSE_URL", default="http://synapse:8008")

# MAS internal listener: health, oauth, admin API
MAS_URL: str = cfg("MAS_URL", default="http://mas:8081")
MAS_HEALTH_URL: str = cfg("MAS_HEALTH_URL", default="http://mas:8081")
# Admin API client, shared with MAS via the environment. ID is required to be ULID.
MAS_ADMIN_CLIENT_ID: str = cfg("MAS_ADMIN_CLIENT_ID", default="")
MAS_ADMIN_CLIENT_SECRET: str = cfg("MAS_ADMIN_CLIENT_SECRET", default="")
SYNAPSE_BOT_USERNAME: str = cfg("SYNAPSE_BOT_USERNAME", default="matrixrmapi-bot")
WEB_CONCURRENCY: int = cfg("WEB_CONCURRENCY", default=1, cast=int)

INIT_MAX_ATTEMPTS: int = cfg("INIT_MAX_ATTEMPTS", default=5, cast=int)
INIT_RETRY_WAIT: float = cfg("INIT_RETRY_WAIT", default=5.0, cast=float)
SERVICE_WAIT_RETRIES: int = cfg("SERVICE_WAIT_RETRIES", default=12, cast=int)
SERVICE_WAIT_INTERVAL: float = cfg("SERVICE_WAIT_INTERVAL", default=5.0, cast=float)


@functools.cache
def get_manifest() -> dict[str, Any]:
    """Get manifest contents"""
    pth = Path("/pvarki/kraftwerk-init.json")
    if not pth.exists():
        return {
            "deployment": "manifest_notfound",
            "rasenmaeher": {
                "init": {
                    "base_uri": "https://localmaeher.dev.pvarki.fi:4439/",
                    "csr_jwt": "",
                },
                "mtls": {"base_uri": "https://mtls.localmaeher.dev.pvarki.fi:4439/"},
                "certcn": "rasenmaeher",
            },
            "product": {
                "dns": "matrix.localmaeher.dev.pvarki.fi",
                "api": "https://matrix.localmaeher.dev.pvarki.fi:4626/",
                "uri": "https://matrix.localmaeher.dev.pvarki.fi:4626/",
            },
        }
    data = json.loads(pth.read_text(encoding="utf-8"))
    return cast(dict[str, Any], data)


def get_server_domain() -> str:
    """Derive Matrix server_name by stripping the first DNS label from product DNS.

    E.g. 'matrix.golden-monkey.dev.pvarki.fi' -> 'golden-monkey.dev.pvarki.fi'
    """
    dns: str = get_manifest()["product"]["dns"]
    return ".".join(dns.split(".")[1:])
