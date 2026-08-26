"""Test the product interoperability endpoints"""

import logging
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from matrixrmapi import config

from .conftest import APP

LOGGER = logging.getLogger(__name__)

# pylint: disable=redefined-outer-name

PEER_CN = "bl.harjoitus1.pvarki.fi"
PAYLOAD = {"certcn": PEER_CN, "x509cert": "-----BEGIN CERTIFICATE-----\\nx\\n"}


@pytest.fixture
def isolated_files(tmp_path: Path) -> Generator[Path, None, None]:
    """Point the registry and token files at a temp dir."""
    orig_products = config.INTEROP_PRODUCTS_FILE
    orig_token = config.BATTLELOG_CREDENTIALS_FILE
    config.INTEROP_PRODUCTS_FILE = tmp_path / "interop_products.json"
    config.BATTLELOG_CREDENTIALS_FILE = tmp_path / "battlelog_bot_credentials.json"
    yield tmp_path
    config.INTEROP_PRODUCTS_FILE = orig_products
    config.BATTLELOG_CREDENTIALS_FILE = orig_token


def test_add_requires_a_cert(isolated_files: Path) -> None:
    """Without an mTLS header the endpoint must not be reachable"""
    client = TestClient(APP)
    assert client.post("/api/v1/interop/add", json=PAYLOAD).status_code == 403


def test_add_requires_rasenmaeher(isolated_files: Path, mtlsclient: TestClient) -> None:
    """Only RASENMAEHER may grant interop, any other CN gets 403"""
    assert mtlsclient.post("/api/v1/interop/add", json=PAYLOAD).status_code == 403


def test_authz_refuses_unregistered_product(
    isolated_files: Path, mtlsclient: TestClient
) -> None:
    """A product RASENMAEHER never granted interop to must not get a token"""
    assert mtlsclient.get("/api/v1/interop/authz").status_code == 403


def test_add_then_authz(
    isolated_files: Path, rm_mtlsclient: TestClient, mtlsclient: TestClient
) -> None:
    """Registered product gets the ingest bot token; before the bot exists, 503"""
    resp = rm_mtlsclient.post(
        "/api/v1/interop/add",
        json={"certcn": "harjoitus1.pvarki.fi", "x509cert": "x"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"]

    # Registration is idempotent
    assert (
        rm_mtlsclient.post(
            "/api/v1/interop/add",
            json={"certcn": "harjoitus1.pvarki.fi", "x509cert": "x"},
        ).status_code
        == 200
    )

    # Synapse startup has not run, so there are no credentials yet: retryable
    assert mtlsclient.get("/api/v1/interop/authz").status_code == 503

    config.BATTLELOG_CREDENTIALS_FILE.write_text(
        '{"user_id": "@battlelog-bot:example.test", "access_token": "syt_dev_bound"}',
        encoding="utf-8",
    )
    resp = mtlsclient.get("/api/v1/interop/authz")
    assert resp.status_code == 200
    # A token, but one registration bound to a device — that is what room keys
    # are shared with.
    assert resp.json() == {
        "type": "bearer-token",
        "token": "syt_dev_bound",
        "username": "@battlelog-bot:example.test",
        "password": None,
        "ro_password": None,
    }
