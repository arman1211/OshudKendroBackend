from rest_framework import viewsets
from ..models.checkout_order import CheckoutOrder
from ..models.order import Order
from ..serializers.ordercheck import CheckoutOrderSerializer
from ..serializers.order import OrderSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.utils.timezone import now
from rest_framework.exceptions import APIException
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from utils.mixins import OrgScopedQuerySetMixin
from ..models.customer_details import CustomerDetails
from rest_framework.views import APIView
from django.db.models import Sum
from decimal import Decimal
from rest_framework.permissions import IsAuthenticated


class CheckoutOrderViewSet(OrgScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = CheckoutOrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            queryset = CheckoutOrder.objects.filter(
                pharmacy_shop=user.organization
            ).order_by("-created_at")
        else:
            queryset = CheckoutOrder.objects.filter(
                pharmacy_shop=user.organization, employee=user
            ).order_by("-created_at")
        date_filter = self.request.query_params.get("date")
        start_date_str = self.request.query_params.get("start_date")
        end_date_str = self.request.query_params.get("end_date")
        status = self.request.query_params.get("status")

        today = datetime.today()
        start = end = None

        if date_filter == "today":
            start = datetime(today.year, today.month, today.day)
            end = start + timedelta(days=1)

        elif date_filter == "yesterday":
            start = datetime(today.year, today.month, today.day) - timedelta(days=1)
            end = datetime(today.year, today.month, today.day)

        elif date_filter == "weekly":
            start = datetime(today.year, today.month, today.day) - timedelta(days=7)
            end = today + timedelta(days=1)

        elif date_filter == "monthly":
            start = datetime(today.year, today.month, 1)
            end = today + timedelta(days=1)

        elif start_date_str and end_date_str:
            try:
                start = datetime.strptime(start_date_str, "%Y-%m-%d")
                end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
            except ValueError:
                return queryset.none()

        if start and end:
            # Make timezone-aware if necessary
            start = make_aware(start)
            end = make_aware(end)
            queryset = queryset.filter(created_at__gte=start, created_at__lt=end)

        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        summary = queryset.aggregate(
            total_sales=Sum("checkout_price"), total_dues=Sum("due_amount")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data

            paginated_data["summary"] = {
                "total_orders": queryset.count(),
                "total_sales": summary.get("total_sales") or Decimal("0.00"),
                "total_dues": summary.get("total_dues") or Decimal("0.00"),
            }
            return Response(paginated_data)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        return Response(
            {
                "results": data,
                "summary": {
                    "total_orders": queryset.count(),
                    "total_revenue": summary.get("total_revenue") or Decimal("0.00"),
                    "total_dues": summary.get("total_dues") or Decimal("0.00"),
                },
            }
        )

    # @action(detail=False, methods=["post"])
    # def checkout(self, request):
    #     print("Raw Request Data:", request.data)
    #     """
    #     Custom action to handle checkout process.
    #     """
    #     try:
    #         user = request.user
    #         employee_id = user.id
    #         pharmacy_shop_id = user.organization
    #         items = request.data.get("items", [])
    #         total_price = sum(item["total_price"] for item in items)

    #         if not employee_id or not pharmacy_shop_id or not items:
    #             return Response(
    #                 {"error": "Missing required fields"},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )

    #         print(request.data)
    #         # Create a new Cart
    #         checkout = CheckoutOrder.objects.create(
    #             pharmacy_shop=pharmacy_shop_id,
    #             employee=employee_id,
    #             checkout_price=total_price,
    #             status="pending",
    #             created_at=now(),
    #         )

    #         # Create CartItems
    #         for item in items:
    #             Order.objects.create(
    #                 checkout=checkout,
    #                 medicine_id=item["medicine"],
    #                 quantity=item["quantity"],
    #                 # price_per_unit=item["price_per_unit"],
    #                 total_price=item["total_price"],
    #                 created_at=now(),
    #             )

    #         return Response(
    #             CheckoutOrderSerializer(checkout).data, status=status.HTTP_201_CREATED
    #         )
    #     except APIException as e:
    #         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         return Response(
    #             {"error": f"Unexpected error: {str(e)}"},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         )


class CustomerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        organization = request.user.organization

        total_customers = (
            CustomerDetails.objects.filter(organization=organization).distinct().count()
        )

        total_due_result = CheckoutOrder.objects.filter(
            pharmacy_shop=organization
        ).aggregate(total=Sum("due_amount"))

        total_due = total_due_result["total"] or Decimal("0.00")

        customers_with_due = (
            CustomerDetails.objects.filter(
                organization=organization,
                checkout_orders__due_amount__gt=0,
            )
            .distinct()
            .count()
        )

        data = {
            "total_customers": total_customers,
            "total_due": total_due,
            "customers_with_due": customers_with_due,
        }

        return Response(data)
