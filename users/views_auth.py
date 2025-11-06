from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .serializers_auth import RegisterSerializer, LoginSerializer, TokenResponseSerializer
from .models import ExpiringToken

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        username = serializer.validated_data.get("username") or email.split("@")[0]

        user = User.objects.create_user(username=username, email=email, password=password)
        # Optionally auto-create profile via signals (if available)
        token_plain, token_obj = ExpiringToken.generate_token_for_user(user, days_valid=365, name="initial")
        resp = {"token": token_plain, "expires_at": token_obj.expires_at}
        return Response(TokenResponseSerializer(resp).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Instead of authenticate(), do manual to support email-as-username patterns robustly
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Email hoặc mật khẩu không đúng."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"detail": "Email hoặc mật khẩu không đúng."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "Tài khoản bị khóa."}, status=status.HTTP_400_BAD_REQUEST)

        # Option: revoke old tokens / or keep multiple tokens. Here we create a new token.
        token_plain, token_obj = ExpiringToken.generate_token_for_user(user, days_valid=365, name="login")
        resp = {"token": token_plain, "expires_at": token_obj.expires_at}
        return Response(TokenResponseSerializer(resp).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # revoke current token used in Authorization header
        auth = request.auth  # with ExpiringTokenAuthentication, request.auth is token obj
        if hasattr(auth, "revoke"):
            auth.revoke()
            return Response({"detail": "Token revoked"}, status=status.HTTP_200_OK)
        # else try parse header and revoke if found
        from .models import ExpiringToken
        header = request.META.get("HTTP_AUTHORIZATION", "")
        parts = header.split()
        if len(parts) == 2:
            token_plain = parts[1]
            tok = ExpiringToken.verify_token(token_plain)
            if tok:
                tok.revoke()
                return Response({"detail": "Token revoked"}, status=status.HTTP_200_OK)
        return Response({"detail": "No token found"}, status=status.HTTP_400_BAD_REQUEST)


class TokenListView(APIView):
    """
    Optional: list tokens of current user (for management). Returns created_at, expires_at, revoked, name.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tokens = request.user.auth_tokens.all().values("id", "name", "created_at", "expires_at", "revoked")
        return Response(list(tokens))