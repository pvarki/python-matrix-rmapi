"""Configurations with .env support"""

from typing import Dict, Any, cast
from pathlib import Path
import json
import functools

from starlette.config import Config

cfg = Config()  # not supporting .env files anymore because https://github.com/encode/starlette/discussions/2446

LOG_LEVEL: int = cfg("LOG_LEVEL", default=20, cast=int)
TEMPLATES_PATH: Path = cfg(
    "TEMPLATES_PATH", cast=Path, default=Path(__file__).parent / "templates"
)

SYNAPSE_URL: str = cfg("SYNAPSE_URL", default="http://synapse:8008")


def _require_nonempty(value: str) -> str:
    if not value:
        raise ValueError("SYNAPSE_REGISTRATION_SECRET must not be empty")
    return value


SYNAPSE_REGISTRATION_SECRET: str = cfg(
    "SYNAPSE_REGISTRATION_SECRET", cast=_require_nonempty
)
SYNAPSE_BOT_USERNAME: str = cfg("SYNAPSE_BOT_USERNAME", default="matrixrmapi-bot")
SYNAPSE_TOKEN_FILE: Path = cfg(
    "SYNAPSE_TOKEN_FILE",
    cast=Path,
    default=Path("/data/persistent/synapse_admin_token"),
)

# Read-only ingest bot handed to BattleLog over the product interop API. It is a
# plain local user, not a server admin: its token can only read and write the
# rooms it has been joined to.
# "-ingest" rather than "-bot": an earlier iteration created battlelog-bot with a
# device-less token, and Synapse keeps a localpart reserved even after the account
# is deactivated, so a bot that can hold encryption keys needs its own name.
BATTLELOG_BOT_USERNAME: str = cfg("BATTLELOG_BOT_USERNAME", default="battlelog-ingest")
# Credentials BattleLog logs in with. A password rather than a ready-made access
# token because logging in is what gets it a *device*, and a device is what other
# clients share end-to-end encryption keys with.
BATTLELOG_CREDENTIALS_FILE: Path = cfg(
    "BATTLELOG_CREDENTIALS_FILE",
    cast=Path,
    default=Path("/data/persistent/battlelog_bot_credentials.json"),
)
# Cert CNs of products RASENMAEHER has granted interop with us. A file rather than
# app.state because gunicorn runs several workers and /interop/add may land on a
# different one than the /interop/authz that follows it.
INTEROP_PRODUCTS_FILE: Path = cfg(
    "INTEROP_PRODUCTS_FILE",
    cast=Path,
    default=Path("/data/persistent/interop_products.json"),
)


@functools.cache
def get_manifest() -> Dict[str, Any]:
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
    return cast(Dict[str, Any], data)


def get_server_domain() -> str:
    """Derive Matrix server_name by stripping the first DNS label from product DNS.

    E.g. 'matrix.golden-monkey.dev.pvarki.fi' -> 'golden-monkey.dev.pvarki.fi'
    """
    dns: str = get_manifest()["product"]["dns"]
    return ".".join(dns.split(".")[1:])
