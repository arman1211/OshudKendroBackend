from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsBusinessAgent, IsCompanyAdmin
from ..serializers import (
    CustomerCreationSerializer,
    OrganizationSerializer,
    BusinessAgentCreationSerializer,
    AgentCreatedUserSerializer,
)
from ..models import Organization, User
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics


class BusinessAgentCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    serializer_class = BusinessAgentCreationSerializer


class CustomerCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, IsBusinessAgent]
    serializer_class = CustomerCreationSerializer

    @swagger_auto_schema(request_body=CustomerCreationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            organization = serializer.save()
            return Response(
                OrganizationSerializer(organization).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentCustomerListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAgent]
    serializer_class = OrganizationSerializer

    def get(self, request, *args, **kwargs):
        onboarded_organizations = Organization.objects.filter(created_by=request.user)
        serializer = self.serializer_class(onboarded_organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AgentCreatedUsersListView(generics.ListAPIView):
    serializer_class = AgentCreatedUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        agent = self.request.user
        return User.objects.filter(created_by=agent).order_by("-created_at")
