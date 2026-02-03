"""pytest automagics"""

from typing import Generator, Dict
import logging
import os
import uuid

from libpvarki.logging import init_logging
import pytest
from fastapi.testclient import TestClient

from rmfpapi.app import get_app
from rmfpapi.config import get_manifest

# Default is "ecs" and it's not great for tests
os.environ["LOG_CONSOLE_FORMATTER"] = "local"
init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
APP = get_app()


@pytest.fixture
def mtlsclient() -> Generator[TestClient, None, None]:
    """Fake the NGinx header"""
    client = TestClient(
        APP,
        headers={
            "X-ClientCert-DN": "CN=harjoitus1.pvarki.fi,O=harjoitus1.pvarki.fi,L=KeskiSuomi,ST=Jyvaskyla,C=FI",
        },
    )
    yield client


@pytest.fixture
def rm_mtlsclient() -> Generator[TestClient, None, None]:
    """Fake the NGinx header"""
    manifest = get_manifest()
    rm_cn = manifest["rasenmaeher"]["certcn"]
    client = TestClient(
        APP,
        headers={
            "X-ClientCert-DN": f"CN={rm_cn},O=harjoitus1.pvarki.fi,L=KeskiSuomi,ST=Jyvaskyla,C=FI",
        },
    )
    yield client


def create_user_dict(callsign: str) -> Dict[str, str]:
    """return valid user dict for crud operations"""
    return {"uuid": str(uuid.uuid4()), "callsign": callsign, "x509cert": "FIXME: insert dummy cert in CFSSL encoding"}


@pytest.fixture(scope="session")
def norppa11() -> Dict[str, str]:
    """Session scoped user dict (to keep same UUID)"""
    return create_user_dict("NORPPA11a")
