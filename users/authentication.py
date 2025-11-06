import requests
from cachetools import TTLCache, cached
from jose import jwt, JWTError

from django.conf import settings
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model

User = get_user_model()

JWKS_CACHE = TTLCache(maxsize=1, ttl=3600)

@cached(JWKS_CACHE)
def get_jwks():
    domain = settings.AUTH0_DOMAIN.rstrip('/')
    jwks_url = f"https://{domain}/.well-known/jwks.json"
    r = requests.get(jwks_url, timeout=5)
    r.raise_for_status()
    return r.json()

def fetch_userinfo(access_token: str) -> dict:
    """Fallback: call Auth0 userinfo endpoint to obtain claims (may include email)."""
    domain = settings.AUTH0_DOMAIN.rstrip('/')
    url = f"https://{domain}/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

class Auth0JSONWebTokenAuthentication(authentication.BaseAuthentication):
    """
    Validate Authorization: Bearer <access_token> issued by Auth0 (RS256).
    On success, returns (user, token). If user does not exist locally, create it.
    """
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header or auth_header[0].lower() != b'bearer':
            return None

        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        token = auth_header[1].decode('utf-8')

        try:
            payload = self._validate_token(token)
        except Exception as exc:
            raise exceptions.AuthenticationFailed(f"Token validation error: {str(exc)}")

        # Try to get email from token; if not present, attempt userinfo
        email = payload.get("email")
        sub = payload.get("sub")

        if not email:
            info = fetch_userinfo(token)
            email = info.get("email") or email
            name = info.get("name")
        else:
            name = payload.get("name")

        # 1) Try match by email
        user = None
        if email:
            try:
                user = User.objects.filter(email__iexact=email).first()
            except Exception:
                user = None

        # 2) If not found by email, try match by external_id stored in profile
        if not user and sub:
            user = User.objects.filter(profile__external_id=sub).first()

        # 3) If still not found, create a new user
        if not user:
            username = None
            if email:
                username = email.split("@")[0]
                user, created = User.objects.get_or_create(email=email, defaults={"username": username})
            else:
                username = (sub or "auth0user").replace("|", "_")
                user, created = User.objects.get_or_create(username=username, defaults={"email": ""})

        # 4) Update user name if available and blank
        if name and (not user.get_full_name()):
            try:
                parts = name.split()
                user.first_name = parts[0]
                user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                user.save(update_fields=["first_name", "last_name"])
            except Exception:
                pass

        # 5) Ensure profile exists and update external_id / is_service_account
        profile = None
        try:
            profile = user.profile
        except Exception:
            from .models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)

        updated = False
        if sub and profile.external_id != sub:
            profile.external_id = sub
            updated = True

        # Mark as service account for common Auth0 client patterns:
        # - legacy: startswith "client|"
        # - new pattern: endswith "@clients" (as seen in your tokens)
        # You can extend this test if you have other patterns.
        is_service = False
        if sub:
            s = str(sub)
            if s.startswith("client|") or s.endswith("@clients"):
                is_service = True

        if is_service and not profile.is_service_account:
            profile.is_service_account = True
            updated = True

        if updated:
            profile.save(update_fields=["external_id", "is_service_account", "updated_at"])

        return (user, token)

    def _validate_token(self, token: str) -> dict:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTError("No 'kid' in token header")

        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        if key is None:
            raise JWTError("Unable to find matching JWK")

        algorithms = ["RS256"]
        issuer = f"https://{settings.AUTH0_DOMAIN}/"
        audience = settings.AUTH0_AUDIENCE

        payload = jwt.decode(token, key, algorithms=algorithms, audience=audience, issuer=issuer)
        return payload