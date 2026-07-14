"""Package level tests"""

from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from matrixrmapi import __version__
from .conftest import APP


def test_version() -> None:
    """Make sure version matches expected"""
    assert __version__ == "1.3.0"  # x-release-please-version


def test_healthcheck_not_initialised(mtlsclient: TestClient) -> None:
    """Without the initialization the service reports unhealthy"""
    resp = mtlsclient.get("/api/v1/healthcheck")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["healthy"] is False


def test_healthcheck_healthy(mtlsclient: TestClient) -> None:
    """With integration initialised and Synapse/MAS responding the service reports healthy"""
    APP.state.synapse = AsyncMock()
    APP.state.rooms = {"space": "!space:x"}
    try:
        with patch(
            "matrixrmapi.api.healthcheck.httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = httpx.Response(
                200, request=httpx.Request("GET", "http://x/health")
            )
            resp = mtlsclient.get("/api/v1/healthcheck")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["healthy"] is True
    finally:
        del APP.state.synapse
        del APP.state.rooms


def test_healthcheck_synapse_down(mtlsclient: TestClient) -> None:
    """A failing Synapse health endpoint makes the service unhealthy"""
    APP.state.synapse = AsyncMock()
    APP.state.rooms = {"space": "!space:x"}
    try:
        with patch(
            "matrixrmapi.api.healthcheck.httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.side_effect = httpx.ConnectError("boom")
            resp = mtlsclient.get("/api/v1/healthcheck")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["healthy"] is False
    finally:
        del APP.state.synapse
        del APP.state.rooms
