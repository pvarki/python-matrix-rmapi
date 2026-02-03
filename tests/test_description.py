"""Test description endpoint"""

import logging

import pytest
from fastapi.testclient import TestClient

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize("lang", ["en", "fi"])
def test_get_description(mtlsclient: TestClient, lang: str) -> None:
    """Check getting the description"""
    resp = mtlsclient.get(f"/api/v1/description/{lang}")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["shortname"] == "fake"
    assert payload["language"] == lang
