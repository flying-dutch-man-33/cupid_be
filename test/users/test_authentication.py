import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

# Import the authentication class and the Profile view from your project.
# Nếu module path khác, sửa import tương ứng:
from users.authentication import Auth0JSONWebTokenAuthentication
from users.views import ProfileView

User = get_user_model()


@pytest.mark.django_db
def test_profile_view_authenticated(monkeypatch):
    """
    Patch the authentication class to return a valid User, then call the
    ProfileView and assert we get HTTP 200 and the expected email in response.
    """
    # Create a real user in DB
    user = User.objects.create_user(username="t_test", email="t_test@example.com", password="password")

    # Create a fake authenticate method that returns (user, None)
    def fake_authenticate(self, request):
        return (user, None)

    monkeypatch.setattr(Auth0JSONWebTokenAuthentication, "authenticate", fake_authenticate)

    # Build request and call view
    rf = RequestFactory()
    request = rf.get("/api/profile/", HTTP_AUTHORIZATION="Bearer faketoken")
    response = ProfileView.as_view()(request)

    # DRF view should return a Response with .status_code and .data
    assert response.status_code == 200
    # Response may contain serializer data in .data
    assert isinstance(response.data, dict)
    assert response.data.get("email") == "t_test@example.com"


@pytest.mark.django_db
def test_profile_view_invalid_token(monkeypatch):
    """
    Patch the authentication class to raise AuthenticationFailed and assert
    the view returns 401 (or appropriate unauthorized response).
    """
    def fake_auth_fail(self, request):
        raise AuthenticationFailed("invalid token")

    monkeypatch.setattr(Auth0JSONWebTokenAuthentication, "authenticate", fake_auth_fail)

    rf = RequestFactory()
    request = rf.get("/api/profile/", HTTP_AUTHORIZATION="Bearer invalid")
    response = ProfileView.as_view()(request)

    # AuthenticationFailed should result in 401 Unauthorized
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_profile_view_force_authenticate():
    """
    Use APIClient.force_authenticate to simulate an authenticated request
    and confirm the profile endpoint returns the logged-in user's data.
    """
    user = User.objects.create_user(username="force_user", email="force@example.com", password="password")
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/profile/")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("email") == "force@example.com"
    assert data.get("username") == "force_user"