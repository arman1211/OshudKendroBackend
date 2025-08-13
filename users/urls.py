from django.urls import path, include
from .views.auth import (
    LoginView,
    RegisterView,
    EmailVerifyView,
    PasswordResetRequestView,
    PasswordResetView,
)
from users.views.profile import ProfileAPIView
from users.views.agent import (
    CustomerCreateAPIView,
    AgentCustomerListAPIView,
    BusinessAgentCreateAPIView,
    AgentCreatedUsersListView,
)
from users.views.organization import (
    OrganizationViewset,
    OrganizationUserViewSet,
    OrganizationGetOrUpdateView,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"organizations", OrganizationViewset)
router.register(
    r"organization/users", OrganizationUserViewSet, basename="organization-users"
)


urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="reg"),
    path("login/", LoginView.as_view(), name="login"),
    path("email_verify/", EmailVerifyView.as_view(), name="email_verify"),
    path(
        "reset_pass_req/", PasswordResetRequestView.as_view(), name="reset_password_req"
    ),
    path("reset_pass/", PasswordResetView.as_view(), name="reset_password"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("customers/create/", CustomerCreateAPIView.as_view(), name="customer-create"),
    path("agent/create/", BusinessAgentCreateAPIView.as_view(), name="agent-create"),
    path(
        "customers/my-list/",
        AgentCustomerListAPIView.as_view(),
        name="agent-customer-list",
    ),
    path(
        "users/my-list/",
        AgentCreatedUsersListView.as_view(),
        name="agent-user-list",
    ),
    path(
        "organization/<int:pk>/get-or-update/",
        OrganizationGetOrUpdateView.as_view(),
        name="organization-get-or-update",
    ),
]
