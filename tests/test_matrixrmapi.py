"""Package level tests"""

from fastapi.testclient import TestClient
from matrixrmapi import __version__


def test_version() -> None:
    """Make sure version matches expected"""
    assert __version__ == "0.0.1"


def test_healthcheck(mtlsclient: TestClient) -> None:
    """Check that health-check works"""
    resp = mtlsclient.get("/api/v1/healthcheck")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["healthy"] is True
