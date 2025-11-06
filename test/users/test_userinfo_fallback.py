import pytest
import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient

import users.authentication as auth_mod
from users.authentication import fetch_userinfo
from users.authentication import Auth0JSONWebTokenAuthentication

User = get_user_model()


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()


@pytest.mark.django_db
def test_fetch_userinfo_returns_json(monkeypatch):
    """
    Unit test for the module-level fetch_userinfo function:
    - mock requests.get to return a fake userinfo JSON
    - assert fetch_userinfo returns the expected dict
    """
    fake_userinfo = {
        "sub": "auth0|123456",
        "email": "fetched@example.com",
        "email_verified": True,
        "nickname": "fetched"
    }

    # Patch requests.get which is used inside fetch_userinfo
    monkeypatch.setattr("requests.get", lambda url, headers=None, timeout=None: FakeResponse(fake_userinfo))
    userinfo = fetch_userinfo("fake-access-token")
    assert isinstance(userinfo, dict)
    assert userinfo["email"] == "fetched@example.com"
    assert userinfo["sub"] == "auth0|123456"


@pytest.mark.django_db
def test_profile_view_with_missing_email_uses_userinfo(monkeypatch):
    """
    Integration-style test that simulates the fallback path:
    - monkeypatch the module-level fetch_userinfo to return an email
    - monkeypatch Auth0JSONWebTokenAuthentication._validate_token to return payload without email
    - call GET /api/profile/ with a bearer token and assert 200 and correct email in response
    """
    # Arrange: fake fetch_userinfo (module-level)
    def fake_fetch_userinfo(access_token):
        return {
            "sub": "auth0|fallback123",
            "email": "fallback@example.com",
            "email_verified": True,
            "nickname": "fallback"
        }

    monkeypatch.setattr(auth_mod, "fetch_userinfo", fake_fetch_userinfo)

    # Arrange: fake _validate_token to simulate token missing email claim
    def fake_validate_token(self, token):
        # Return payload without "email" so authenticate() triggers fetch_userinfo fallback
        return {
            "sub": "auth0|fallback123",
            "name": "fallback"
        }

    monkeypatch.setattr(Auth0JSONWebTokenAuthentication, "_validate_token", fake_validate_token)

    # Act: call the endpoint
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer faketoken")
    resp = client.get("/api/profile/")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("email") == "fallback@example.com"
    # username created from email local part in your authenticate logic
    assert data.get("username") == "fallback"