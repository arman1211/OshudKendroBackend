from django.contrib.postgres.search import TrigramSimilarity
from ..models.product import Medicine
from ..models.unitmedicine import UnitPriceMedicine
from ..serializers.medicine import MedicineSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from users.permissions import (
    IsOrganizationAdmin,
    IsOrganizationEmployee,
    IsOrganizationManager,
    InventoryPermission,
    IsCompanyAdmin,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.swagger_schema import search_param
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import csv, io
from ..models import Medicine, Inventory, GenericName, Category
from django.db.models import Exists, OuterRef
from django.db import transaction


class MedicineCSVUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        organization = request.user.organization

        if not file.name.endswith(".csv"):
            return Response(
                {"error": "Please upload a CSV file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decoded_file = file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        try:
            with transaction.atomic():
                for row in reader:
                    generic_name, _ = GenericName.objects.get_or_create(
                        name=row["Generic Name"].strip()
                    )
                    category, _ = Category.objects.get_or_create(
                        name=row["Category"].strip()
                    )

                    medicine, _ = Medicine.objects.get_or_create(
                        name=row["Name"].strip(),
                        defaults={
                            "generic_name": generic_name,
                            "category": category,
                            "dosage": row["Dosage"],
                            "brand": row.get("Brand", ""),
                            "dosage_form": row.get("Dosage Form", ""),
                            "strips_per_box": int(row["Strip per Box"]),
                            "pieces_per_strip": int(row["Pieces per Strip"]),
                            "pieces_per_box": int(row["Pieces per Box"]),
                        },
                    )

                    Inventory.objects.update_or_create(
                        medicine=medicine,
                        organization=organization,
                        defaults={
                            "buying_price": float(row["Buying Price"]),
                            "selling_price": float(row["Selling Price"]),
                        },
                    )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Medicines imported successfully"},
            status=status.HTTP_201_CREATED,
        )


class MedicineViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    pagination_class = None

    def get_queryset(self):

        user_org = self.request.user.organization
        inventory_exists_subquery = Inventory.objects.filter(
            medicine=OuterRef("pk"), organization=user_org
        )
        queryset = (
            super()
            .get_queryset()
            .annotate(is_in_inventory=Exists(inventory_exists_subquery))
        )
        search_param = self.request.query_params.get("q")
        if search_param:
            queryset = (
                queryset.annotate(similarity=TrigramSimilarity("name", search_param))
                .filter(similarity__gt=0.3)
                .order_by("-similarity")
            )

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(manual_parameters=[search_param])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
