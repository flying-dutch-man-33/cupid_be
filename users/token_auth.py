from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import ExpiringToken

class ExpiringTokenAuthentication(authentication.BaseAuthentication):
    """
    Authentication accepting:
    - Authorization: Token <token>
    - Authorization: Bearer <token>
    Returns (user, token_obj) on success.
    """
    keyword_tokens = ("Token", "Bearer")

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header:
            return None

        if len(header) == 1:
            raise exceptions.AuthenticationFailed("Invalid token header. No credentials provided.")
        if len(header) > 2:
            raise exceptions.AuthenticationFailed("Invalid token header. Token string should not contain spaces.")

        scheme = header[0].decode()
        token = header[1].decode()

        if scheme not in self.keyword_tokens:
            return None

        tok_obj = ExpiringToken.verify_token(token)
        if not tok_obj:
            raise exceptions.AuthenticationFailed("Invalid or expired token.")
        user = tok_obj.user
        return (user, tok_obj)