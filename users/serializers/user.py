from rest_framework import serializers
from ..models.user import User
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        exclude = ["password"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "user_type", "role")

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            user_type=validated_data["user_type"],
            role=validated_data["role"],
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class AgentCreatedUserSerializer(serializers.ModelSerializer):
    pharmacy_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "user_type",
            "role",
            "pharmacy_name",
        ]
