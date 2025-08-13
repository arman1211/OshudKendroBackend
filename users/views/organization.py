from ..serializers.organization import (
    OrganizationSerializer,
    OrganizationUserSerializer,
)
from ..models.organization import Organization
from rest_framework import viewsets, generics
from users.permissions import IsBusinessAgent, IsOrganizationAdmin
from rest_framework.permissions import IsAuthenticated, AllowAny
from users.models import User


class OrganizationViewset(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    pagination_class = None
    permission_classes = [IsBusinessAgent]


class OrganizationGetOrUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_object(self):
        return self.request.user.organization


class OrganizationUserViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationUserSerializer
    permission_classes = [IsOrganizationAdmin]
    pagination_class = None

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save()
