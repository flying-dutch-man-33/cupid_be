from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "bio",
            "avatar_url",
            "indirect_teaser",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "username", "email"]