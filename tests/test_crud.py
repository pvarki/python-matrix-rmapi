"""Test the CRUD operations"""

from typing import Dict
import logging
from fastapi.testclient import TestClient

from .conftest import APP

LOGGER = logging.getLogger(__name__)


# pylint: disable=redefined-outer-name


def test_unauth(norppa11: Dict[str, str]) -> None:
    """Check that unauth call to auth endpoint fails"""
    client = TestClient(APP)
    resp = client.post("/api/v1/users/created", json=norppa11)
    assert resp.status_code == 403


def test_create(norppa11: Dict[str, str], rm_mtlsclient: TestClient) -> None:
    """Check that adding user works"""
    resp = rm_mtlsclient.post("/api/v1/users/created", json=norppa11)
    assert resp.status_code == 200
    payload = resp.json()
    assert "success" in payload
    assert payload["success"]


def test_update(norppa11: Dict[str, str], rm_mtlsclient: TestClient) -> None:
    """Check that updating user works"""
    resp = rm_mtlsclient.put("/api/v1/users/updated", json=norppa11)
    assert resp.status_code == 200
    payload = resp.json()
    assert "success" in payload
    assert payload["success"]


def test_revoke(norppa11: Dict[str, str], rm_mtlsclient: TestClient) -> None:
    """Check that revoking user works"""
    resp = rm_mtlsclient.post("/api/v1/users/revoked", json=norppa11)
    assert resp.status_code == 200
    payload = resp.json()
    assert "success" in payload
    assert payload["success"]


def test_promote(norppa11: Dict[str, str], rm_mtlsclient: TestClient) -> None:
    """Check that promoting user works"""
    resp = rm_mtlsclient.post("/api/v1/users/promoted", json=norppa11)
    assert resp.status_code == 200
    payload = resp.json()
    assert "success" in payload
    assert payload["success"]


def test_demote(norppa11: Dict[str, str], rm_mtlsclient: TestClient) -> None:
    """Check that demoting user works"""
    resp = rm_mtlsclient.post("/api/v1/users/demoted", json=norppa11)
    assert resp.status_code == 200
    payload = resp.json()
    assert "success" in payload
    assert payload["success"]
