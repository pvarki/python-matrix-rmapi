"""Test the CRUD operations"""

from typing import Dict
import logging
import uuid
from fastapi.testclient import TestClient

from matrixrmapi.config import get_server_domain
from matrixrmapi.types import AdminAction
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


# ---------------------------------------------------------------------------
# Deferred-queue behaviour (Synapse not yet ready)
# ---------------------------------------------------------------------------


def _unique_user() -> Dict[str, str]:
    """Return a user dict with a unique callsign to avoid state collisions."""
    tag = uuid.uuid4().hex[:6]
    return {
        "uuid": str(uuid.uuid4()),
        "callsign": f"queue{tag}",
        "x509cert": "FIXME: dummy",
    }


def test_promote_queues_uid_when_synapse_not_ready(rm_mtlsclient: TestClient) -> None:
    """When Synapse is not yet initialised, /promoted must enqueue the uid."""
    user = _unique_user()
    resp = rm_mtlsclient.post("/api/v1/users/promoted", json=user)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    uid = f"@{user['callsign'].lower()}:{get_server_domain()}"
    pending: Dict[str, AdminAction] = getattr(APP.state, "pending_promotions", {})
    assert pending.get(uid) is AdminAction.PROMOTE


def test_demote_queues_uid_when_synapse_not_ready(rm_mtlsclient: TestClient) -> None:
    """When Synapse is not yet initialised, /demoted must enqueue the uid."""
    user = _unique_user()
    resp = rm_mtlsclient.post("/api/v1/users/demoted", json=user)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    uid = f"@{user['callsign'].lower()}:{get_server_domain()}"
    pending: Dict[str, AdminAction] = getattr(APP.state, "pending_promotions", {})
    assert pending.get(uid) is AdminAction.DEMOTE


def test_demote_overwrites_pending_promote(rm_mtlsclient: TestClient) -> None:
    """If a user is promoted then demoted before Synapse is ready, only demote survives."""
    user = _unique_user()
    uid = f"@{user['callsign'].lower()}:{get_server_domain()}"

    rm_mtlsclient.post("/api/v1/users/promoted", json=user)
    rm_mtlsclient.post("/api/v1/users/demoted", json=user)

    pending: Dict[str, AdminAction] = getattr(APP.state, "pending_promotions", {})
    assert pending.get(uid) is AdminAction.DEMOTE
