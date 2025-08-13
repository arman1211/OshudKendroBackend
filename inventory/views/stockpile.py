from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework import generics
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from ..models.stockpile import Inventory
from ..serializers.stockpile import InventorySerializer, InventoryCreateSerializer
from users.permissions import InventoryPermission, IsCompanyAdmin
from utils.mixins import OrgScopedQuerySetMixin
from utils.swagger_schema import search_param
from rest_framework.response import Response
from inventory.models import Inventory
from django.db.models import Q, F
from django.db.models.functions import Greatest
from django.contrib.postgres.search import TrigramSimilarity


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    permission_classes = [IsAuthenticated]
    allowed_methods = ["get", "post"]

    def get_serializer_class(self):
        if self.action == "create":
            return InventoryCreateSerializer
        return InventorySerializer

    def get_queryset(self):
        user_org = self.request.user.organization_id
        search_param = self.request.query_params.get("q")

        queryset = (
            super()
            .get_queryset()
            .select_related("medicine", "organization", "medicine__generic_name")
            .filter(organization_id=user_org)
        )

        if search_param:
            queryset = (
                queryset.annotate(
                    sim_name=TrigramSimilarity("medicine__name", search_param),
                    sim_generic=TrigramSimilarity(
                        "medicine__generic_name__name", search_param
                    ),
                    similarity=Greatest(F("sim_name"), F("sim_generic")),
                )
                .filter(similarity__gt=0.3)
                .order_by("-similarity")
            )

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inventory = Inventory.objects.create(
            medicine=serializer.validated_data["medicine"],
            organization=request.user.organization,
            quantity=0,
            stock_alert_qty=0,
        )
        inventory.save()

        # Return full inventory data with medicine_detail
        output_serializer = InventorySerializer(inventory, context={"request": request})
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @swagger_auto_schema(manual_parameters=[search_param])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class InventoryQuantityView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Inventory.objects.all()

    def get(self, request, *args, **kwargs):
        inventory = self.get_object()
        return Response({"quantity": inventory.quantity})
