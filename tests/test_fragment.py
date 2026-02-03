"""Test the HTML fragment"""

from typing import Dict
import logging
import base64

from fastapi.testclient import TestClient
import pytest

from rmfpapi.config import get_manifest
from .conftest import APP

LOGGER = logging.getLogger(__name__)


def test_unauth(norppa11: Dict[str, str]) -> None:
    """Check that unauth call to auth endpoint fails"""
    client = TestClient(APP)
    resp = client.post("/api/v1/clients/fragment", json=norppa11)
    assert resp.status_code == 403


def test_get_fragment(norppa11: Dict[str, str], mtlsclient: TestClient) -> None:
    """Check that getting fragment works"""
    resp = mtlsclient.post("/api/v1/clients/fragment", json=norppa11)
    assert resp.status_code == 200
    payload = resp.json()
    for fpl in payload:
        assert fpl["title"]
        assert fpl["filename"]
        assert fpl["data"]
        data = str(fpl["data"])
        assert data.startswith("data:")
        _, b64data = data.split(",")
        dec = base64.b64decode(b64data)
        assert dec


def test_get_admin_fragment(mtlsclient: TestClient) -> None:
    """Check that getting admin fragment works"""
    resp = mtlsclient.get("/api/v1/admins/fragment")
    assert resp.status_code == 200
    payload = resp.json()
    assert "html" in payload
    assert payload["html"] == "<p>Hello to the admin</p>"


@pytest.mark.parametrize("lang", ["en", "fi", "sv"])
def test_get_v2_user_markdown(norppa11: Dict[str, str], rm_mtlsclient: TestClient, lang: str) -> None:
    """Check that getting v2 user markdown works"""
    manifest = get_manifest()
    dname = manifest["deployment"]
    resp = rm_mtlsclient.post(f"/api/v2/clients/{lang}/info.md", json=norppa11)
    assert resp.status_code == 200
    assert dname in resp.text


@pytest.mark.parametrize("lang", ["en", "fi", "sv"])
def test_get_v2_user_markdown_wrongcaller(norppa11: Dict[str, str], mtlsclient: TestClient, lang: str) -> None:
    """Check that getting v2 user markdown fails if not coming from RASENMAEHER"""
    resp = mtlsclient.post(f"/api/v2/clients/{lang}/info.md", json=norppa11)
    assert resp.status_code == 403
