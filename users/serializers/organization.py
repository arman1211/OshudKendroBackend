from rest_framework import serializers
from users.models import User
from ..models.organization import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"


class CustomerCreationSerializer(serializers.Serializer):
    # Organization fields
    pharmacy_name = serializers.CharField(max_length=100)
    pharmacy_address = serializers.CharField()
    pharmacy_contact = serializers.CharField(max_length=15)

    # User (Pharmacy Owner) fields
    owner_first_name = serializers.CharField(max_length=50)
    owner_last_name = serializers.CharField(max_length=50)
    owner_email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):

        pharmacy_name = attrs.get("pharmacy_name")
        pharmacy_contact = attrs.get("pharmacy_contact")

        if Organization.objects.filter(
            name=pharmacy_name, contact_number=pharmacy_contact
        ).exists():
            raise serializers.ValidationError(
                "An organization with this name and contact number already exists."
            )

        return attrs

    def validate_owner_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        business_agent = self.context["request"].user

        # Create the Organization
        organization = Organization.objects.create(
            name=validated_data["pharmacy_name"],
            address=validated_data["pharmacy_address"],
            contact_number=validated_data["pharmacy_contact"],
            created_by=business_agent,
        )

        # Create the User (Pharmacy Owner)
        customer_user = User.objects.create_user(
            email=validated_data["owner_email"],
            password=validated_data["password"],
            first_name=validated_data["owner_first_name"],
            last_name=validated_data["owner_last_name"],
            organization=organization,
            user_type="organization",
            role="admin",
            is_active=True,
            created_by=business_agent,
        )

        return organization


class OrganizationUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "role",
            "role_display",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        request = self.context["request"]
        organization = request.user.organization

        password = validated_data.pop("password", None)
        user = User(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            user_type="organization",
            role=validated_data["role"],
            organization=organization,
            is_active=True,
            created_by=request.user,
        )
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
