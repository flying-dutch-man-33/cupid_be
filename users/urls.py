from django.urls import path
from .views import ProfileView
from .views_auth import RegisterView, LoginView, LogoutView, TokenListView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/tokens/", TokenListView.as_view(), name="auth-tokens"),
]