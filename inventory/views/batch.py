from rest_framework import viewsets
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsOrganizationAdmin
from inventory.models import Batch, Inventory
from inventory.serializers.batch import BatchSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from utils.swagger_schema import inventory_id
from inventory.models import Batch, Inventory
from inventory.serializers.batch import BatchAlertSerializer
from inventory.serializers.stockpile import InventoryAlertSerializer
from rest_framework.generics import ListAPIView
from datetime import timedelta
from django.db.models import F, Q


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        inventory_id = self.request.query_params.get("inventory_id")
        if inventory_id:
            return self.queryset.filter(inventory_id=inventory_id)
        return self.queryset

    @swagger_auto_schema(manual_parameters=[inventory_id])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            batch = self.get_object()
            inventory = batch.inventory

            inventory = Inventory.objects.select_for_update().get(id=inventory.id)

            inventory.quantity -= batch.quantity
            inventory.save()

            return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        return Response(status=status.HTTP_200_OK)


class GenerateBatchNumberView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(manual_parameters=[inventory_id])
    def get(self, request):
        inventory_id = request.query_params.get("inventory_id")
        if not inventory_id:
            return Response(
                {"error": "Inventory ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            inventory = Inventory.objects.get(
                id=inventory_id, organization_id=request.user.organization.id
            )
        except Inventory.DoesNotExist:
            return Response(
                {"error": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND
            )

        existing_batches = inventory.batches.all()

        # Enforce max 3 batches
        if existing_batches.count() >= 3:
            return Response(
                {"error": "Maximum 3 batches allowed for this inventory"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_prefix = "BATCH"

        suffix = "A"
        while True:
            batch_number = f"{base_prefix}-{suffix}"
            if not existing_batches.filter(batch_number=batch_number).exists():
                break
            suffix = chr(ord(suffix) + 1)

        return Response({"batch_number": batch_number}, status=status.HTTP_200_OK)


class BatchPartialUpdateAPI(APIView):

    permission_classes = [IsOrganizationAdmin]

    def patch(self, request, batch_id):
        try:
            with transaction.atomic():
                # Lock both Batch and related Inventory rows
                batch = Batch.objects.select_for_update().get(id=batch_id)
                inventory = Inventory.objects.select_for_update().get(
                    id=batch.inventory.id
                )
                # Process normal fields
                serializer = BatchSerializer(batch, data=request.data, partial=True)
                if not serializer.is_valid():
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                updated_batch = serializer.save()

                if "stock_alert_qty" in request.data:
                    inventory.stock_alert_qty += int(
                        request.data.get("stock_alert_qty")
                    )
                    inventory.save()

                # Handle quantity increment
                if "new_quantity" in request.data:
                    quantity_increment = int(request.data["new_quantity"])
                    if quantity_increment > 0:
                        updated_batch.quantity += quantity_increment
                        updated_batch.save()

                        inventory.quantity += quantity_increment
                        inventory.save()

                return Response(BatchSerializer(updated_batch).data)

        except Batch.DoesNotExist:
            return Response(
                {"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MedicineAlertsView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.query_params.get("alert_type") == "stock":
            return InventoryAlertSerializer
        return BatchAlertSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "alert_type",
                openapi.IN_QUERY,
                required=True,
                type=openapi.TYPE_STRING,
                enum=["stock", "expiry"],
            ),
            openapi.Parameter(
                "expiry_days", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=90
            ),
            openapi.Parameter(
                "status_filter",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by status. For 'expiry': ['Expired', 'Expiring Soon']. For 'stock': ['Stock Out', 'Low Stock'].",
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        try:
            organization = self.request.user.organization
        except AttributeError:
            return Inventory.objects.none()

        alert_type = self.request.query_params.get("alert_type")
        status_filter = self.request.query_params.get("status_filter")
        today = timezone.now().date()

        if alert_type == "stock":
            queryset = Inventory.objects.filter(
                organization=organization, quantity__lte=F("stock_alert_qty")
            )
            if status_filter == "Stock Out":
                queryset = queryset.filter(quantity=0)
            elif status_filter == "Low Stock":
                queryset = queryset.filter(quantity__gt=0)
            return queryset.select_related("medicine", "medicine__generic_name")

        elif alert_type == "expiry":
            expiry_days = int(self.request.query_params.get("expiry_days", 90))
            threshold_date = today + timedelta(days=expiry_days)

            base_query = Q(
                inventory__organization=organization,
                expiry_date__isnull=False,
                expiry_date__lte=threshold_date,
            )

            if status_filter == "Expired":
                queryset = Batch.objects.filter(base_query, expiry_date__lt=today)
            elif status_filter == "Expiring Soon":
                queryset = Batch.objects.filter(base_query, expiry_date__gte=today)
            else:
                queryset = Batch.objects.filter(base_query)

            return queryset.select_related(
                "inventory", "inventory__medicine", "inventory__medicine__generic_name"
            ).order_by("expiry_date")

        return Inventory.objects.none()


class AlertsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            organization = request.user.organization
        except AttributeError:
            return Response(
                {"error": "User is not associated with an organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()

        low_stock_count = Inventory.objects.filter(
            organization=organization, quantity__lte=F("stock_alert_qty")
        ).count()

        ninety_days_from_now = today + timedelta(days=90)
        expiring_soon_count = Batch.objects.filter(
            inventory__organization=organization,
            expiry_date__lte=ninety_days_from_now,
        ).count()

        critical_alert_count = Batch.objects.filter(
            inventory__organization=organization,
            expiry_date__lt=today,
        ).count()

        data = {
            "low_stock_count": low_stock_count,
            "expiring_count": expiring_soon_count,
            "critical_count": critical_alert_count,
        }

        return Response(data, status=status.HTTP_200_OK)
