from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..serializers.dashboard import (
    SalesAndProfitDashboardSerializer,
    DuesDashboardSerializer,
    SupplierDashboardSerializer,
)
from supplier.models import Supplier, SupplierOrder
from ..models.checkout_order import CheckoutOrder
from ..models.checkout_payment import Payment


class SalesAndProfitDashboardApiView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "filter_by",
                openapi.IN_QUERY,
                description="Pre-defined date filter",
                type=openapi.TYPE_STRING,
                enum=["all_time", "today", "this_week", "this_month", "this_year"],
            ),
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Custom start date (format: YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format="date",
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="Custom end date (format: YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format="date",
            ),
        ],
        responses={200: SalesAndProfitDashboardSerializer},
        operation_description="Get aggregated sales and profit data with date-based filtering.",
    )
    def get(self, request, *args, **kwargs):
        filter_by = request.query_params.get("filter_by")
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        queryset = CheckoutOrder.objects.filter(pharmacy_shop=request.user.organization)

        start_date, end_date = None, None

        if filter_by and filter_by != "all_time":
            end_date = timezone.now()
            if filter_by == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif filter_by == "this_week":
                start_date = (end_date - timedelta(days=end_date.weekday())).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif filter_by == "this_month":
                start_date = end_date.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            elif filter_by == "this_year":
                start_date = end_date.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                )

            if start_date:
                queryset = queryset.filter(created_at__range=(start_date, end_date))

        elif start_date_str and end_date_str:
            try:
                start_date = timezone.datetime.strptime(
                    start_date_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.get_current_timezone())
                end_date = (
                    timezone.datetime.strptime(end_date_str, "%Y-%m-%d")
                    + timedelta(days=1)
                ).replace(tzinfo=timezone.get_current_timezone())
                queryset = queryset.filter(created_at__range=(start_date, end_date))
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
                )

        aggregates = queryset.aggregate(
            total_sales=Coalesce(Sum("checkout_price"), Decimal("0.0")),
            total_orders=Count("id"),
            total_dues_in_period=Coalesce(Sum("due_amount"), Decimal("0.0")),
        )

        total_sales = aggregates["total_sales"]
        total_order = aggregates["total_orders"]

        profit_margin = Decimal("0.50")
        total_profit = total_sales * profit_margin
        profit_without_dues = (
            total_sales - aggregates["total_dues_in_period"]
        ) * profit_margin

        num_days = 1
        if start_date and end_date:
            delta = end_date - start_date
            num_days = delta.days + 1
        else:
            first_order = (
                CheckoutOrder.objects.filter(pharmacy_shop=request.user.organization)
                .order_by("created_at")
                .first()
            )
            if first_order:
                delta = timezone.now() - first_order.created_at
                num_days = delta.days + 1

        average_sales = total_sales / num_days if num_days > 0 else Decimal("0.0")

        data = {
            "total_order": total_order,
            "total_sales": total_sales,
            "total_profit": total_profit,
            "profit_without_dues": profit_without_dues,
            "average_sales": average_sales,
        }

        serializer = SalesAndProfitDashboardSerializer(data)
        return Response(serializer.data)


class DuesDashboardApiView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "filter_by",
                openapi.IN_QUERY,
                description="Filter for 'Dues Collected' (today, this_week, etc.)",
                type=openapi.TYPE_STRING,
                enum=["all_time", "today", "this_week", "this_month", "this_year"],
            ),
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Custom start date for 'Dues Collected'",
                type=openapi.TYPE_STRING,
                format="date",
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="Custom end date for 'Dues Collected'",
                type=openapi.TYPE_STRING,
                format="date",
            ),
        ],
        responses={200: DuesDashboardSerializer},
        operation_description="Get aggregated dues data. Note: 'Total Dues' and 'Customers with Dues' reflect the overall \
            current state and are not affected by date filters.",
    )
    def get(self, request, *args, **kwargs):
        filter_by = request.query_params.get("filter_by")
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        base_orders_queryset = CheckoutOrder.objects.filter(
            pharmacy_shop=request.user.organization
        )

        total_dues = base_orders_queryset.filter(due_amount__gt=0).aggregate(
            total=Coalesce(Sum("due_amount"), Decimal("0.0"))
        )["total"]

        customers_with_dues = (
            base_orders_queryset.filter(due_amount__gt=0, customer__isnull=False)
            .values("customer")
            .distinct()
            .count()
        )

        payments_queryset = Payment.objects.filter(
            checkout_order__pharmacy_shop=request.user.organization
        )

        if filter_by and filter_by != "all_time":
            end_date = timezone.now()
            start_date = None
            if filter_by == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif filter_by == "this_week":
                start_date = (end_date - timedelta(days=end_date.weekday())).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif filter_by == "this_month":
                start_date = end_date.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            elif filter_by == "this_year":
                start_date = end_date.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                )

            if start_date:
                payments_queryset = payments_queryset.filter(
                    created_at__range=(start_date, end_date)
                )

        elif start_date_str and end_date_str:
            try:
                start_date = timezone.datetime.strptime(
                    start_date_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.get_current_timezone())
                end_date = (
                    timezone.datetime.strptime(end_date_str, "%Y-%m-%d")
                    + timedelta(days=1)
                ).replace(tzinfo=timezone.get_current_timezone())
                payments_queryset = payments_queryset.filter(
                    created_at__range=(start_date, end_date)
                )
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
                )

        dues_collected = payments_queryset.aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.0"))
        )["total"]

        data = {
            "total_dues": total_dues,
            "dues_collected": dues_collected,
            "customers_with_dues": customers_with_dues,
        }

        serializer = DuesDashboardSerializer(data)
        return Response(serializer.data)


class SupplierDashboardAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "filter_by",
                openapi.IN_QUERY,
                description="Pre-defined date filter",
                type=openapi.TYPE_STRING,
                enum=["all_time", "today", "this_week", "this_month", "this_year"],
            ),
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Custom start date (format: YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format="date",
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="Custom end date (format: YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format="date",
            ),
        ],
        responses={200: SupplierDashboardSerializer},
        operation_description="Get aggregated supplier data with date-based filtering.",
    )
    def get(self, request, *args, **kwargs):
        filter_by = request.query_params.get("filter_by")
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        queryset_orders = SupplierOrder.objects.filter(
            organization=request.user.organization
        )

        if filter_by and filter_by != "all_time":
            end_date = timezone.now()
            start_date = None
            if filter_by == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif filter_by == "this_week":
                start_date = (end_date - timedelta(days=end_date.weekday())).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif filter_by == "this_month":
                start_date = end_date.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            elif filter_by == "this_year":
                start_date = end_date.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                )

            if start_date:
                queryset_orders = queryset_orders.filter(
                    created_at__range=(start_date, end_date)
                )

        elif start_date_str and end_date_str:
            try:
                start_date = timezone.datetime.strptime(
                    start_date_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.get_current_timezone())
                end_date = (
                    timezone.datetime.strptime(end_date_str, "%Y-%m-%d")
                    + timedelta(days=1)
                ).replace(tzinfo=timezone.get_current_timezone())
                queryset_orders = queryset_orders.filter(
                    created_at__range=(start_date, end_date)
                )
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
                )

        total_suppliers = Supplier.objects.filter(
            organization=request.user.organization
        ).count()

        aggregates = queryset_orders.aggregate(
            total_orders_amount=Coalesce(Sum("total_amount"), Decimal("0.00")),
            total_dues=Coalesce(Sum("due_amount"), Decimal("0.00")),
        )

        orders_with_due = queryset_orders.filter(due_amount__gt=0).count()

        data = {
            "total_suppliers": total_suppliers,
            "total_orders_amount": aggregates["total_orders_amount"],
            "total_dues": aggregates["total_dues"],
            "orders_with_due": orders_with_due,
        }

        serializer = SupplierDashboardSerializer(data)
        return Response(serializer.data)
