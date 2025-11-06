from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from azure.identity import DefaultAzureCredential
from dataselectie_proxy.search.clients import AzureSearchServiceClient
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from tests.utils import api_request_with_scopes, to_drf_request

HERE = Path(__file__).parent


@pytest.fixture()
def api_rf() -> APIRequestFactory:
    """Request factory for APIView classes"""
    return APIRequestFactory()


@pytest.fixture()
def api_request() -> WSGIRequest:
    """Return a very basic Request object. This can be used for the APIClient.
    The DRF views use a different request object internally, see `drf_request` for that.
    """
    return api_request_with_scopes([])


@pytest.fixture()
def drf_request(api_request) -> Request:
    """The wrapped WSGI Request as a Django-Rest-Framework request.
    This is the 'request' object that APIView.dispatch() creates.
    """
    return to_drf_request(api_request)


@pytest.fixture()
def api_client() -> APIClient:
    """Return a client that has unhindered access to the API views"""
    api_client = APIClient()
    api_client.default_format = "json"  # instead of multipart
    return api_client


@pytest.fixture()
def common_headers(request) -> dict:
    return {
        "X-Correlation-ID": request.node.name,
        "X-User": "foobar",
        "X-Task-Description": "unittest",
    }


@pytest.fixture(autouse=True)
def mock_default_credential():
    with patch.object(DefaultAzureCredential, "__init__") as mock_credential:
        mock_credential.return_value = None
        yield mock_credential


@dataclass
class AccessToken:
    token: str  # bearer
    expires_on: int


@pytest.fixture(autouse=True)
def mock_fetch_token():
    with patch.object(AzureSearchServiceClient, "_fetch_token") as mock_fetch_token:
        token = AccessToken(token="oauth_token", expires_on=3600)
        mock_fetch_token.return_value = token
        yield mock_fetch_token
