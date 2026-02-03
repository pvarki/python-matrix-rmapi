"""Configurations with .env support"""

from typing import Dict, Any, cast
from pathlib import Path
import json
import functools

from starlette.config import Config

cfg = Config()  # not supporting .env files anymore because https://github.com/encode/starlette/discussions/2446

LOG_LEVEL: int = cfg("LOG_LEVEL", default=20, cast=int)
TEMPLATES_PATH: Path = cfg("TEMPLATES_PATH", cast=Path, default=Path(__file__).parent / "templates")


@functools.cache
def get_manifest() -> Dict[str, Any]:
    """Get manifest contents"""
    pth = Path("/pvarki/kraftwerk-init.json")
    if not pth.exists():
        return {
            "deployment": "manifest_notfound",
            "rasenmaeher": {
                "init": {"base_uri": "https://localmaeher.dev.pvarki.fi:4439/", "csr_jwt": ""},
                "mtls": {"base_uri": "https://mtls.localmaeher.dev.pvarki.fi:4439/"},
                "certcn": "rasenmaeher",
            },
            "product": {
                "dns": "fake.localmaeher.dev.pvarki.fi",
                "api": "https://fake.localmaeher.dev.pvarki.fi:4626/",
                "uri": "https://fake.localmaeher.dev.pvarki.fi:4626/",
            },
        }
    data = json.loads(pth.read_text(encoding="utf-8"))
    return cast(Dict[str, Any], data)
