from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.auth.hashers import make_password, check_password
import random
from users.models.organization import Organization
from django.conf import settings


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = [
        ("company", "Company"),
        ("organization", "Organization"),
    ]

    ROLES = [
        ("admin", "Admin"),
        ("employee", "Employee"),
        ("business_agent", "Revenue Partner"),
        ("manager", "Manager"),
        ("user", "User"),
    ]

    email = models.EmailField(unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarded_customers",
    )
    user_type = models.CharField(max_length=50, choices=USER_TYPES)
    role = models.CharField(max_length=50, choices=ROLES, default="user")
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.pk:
            self.password = make_password(self.password)
            self.email_verification_code = str(random.randint(100000, 999999))
        super(User, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.email_verification_code = str(random.randint(100000, 999999))
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"