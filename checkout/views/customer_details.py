from ..serializers.customer_details import (
    CustomerDetailsSerializer,
    PayTotalDueSerializer,
)
from ..models.customer_details import CustomerDetails
from ..models.checkout_order import CheckoutOrder
from ..serializers.ordercheck import CheckoutOrderSerializer
from ..serializers.checkout_payment import PaymentSerializer
from ..models.checkout_payment import Payment
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework import status

from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from django.db.models import Q, Exists, OuterRef
from utils.mixins import OrgScopedQuerySetMixin, CustomerOrganizationMixin


class CustomerDetailsList(ListAPIView):

    serializer_class = CustomerDetailsSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        organization = self.request.user.organization
        queryset = CustomerDetails.objects.filter(organization=organization)

        # search = self.request.query_params.get("search", None)
        # if search:
        #     queryset = queryset.filter(
        #         Q(name__icontains=search) | Q(contact__icontains=search)
        #     )

        return queryset.order_by("-id")


class CustomerListView(ListAPIView):
    """List all customers with their due amounts"""

    serializer_class = CustomerDetailsSerializer

    def get_queryset(self):
        organization = self.request.user.organization

        due_orders_subquery = CheckoutOrder.objects.filter(
            pharmacy_shop=organization, customer=OuterRef("pk"), due_amount__gt=0
        )

        queryset = (
            CustomerDetails.objects.filter(organization=organization)
            .distinct()
            .annotate(has_due=Exists(due_orders_subquery))
        )

        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(contact__icontains=search)
            )

        return queryset.order_by("-has_due", "-id")


class CustomerDetailView(RetrieveAPIView):
    """Get customer details with their orders and payments"""

    queryset = CustomerDetails.objects.all()
    serializer_class = CustomerDetailsSerializer

    def retrieve(self, request, *args, **kwargs):
        customer = self.get_object()
        serializer = self.get_serializer(customer)

        # Get customer's orders
        orders = CheckoutOrder.objects.filter(customer=customer).order_by("-created_at")
        orders_serializer = CheckoutOrderSerializer(orders, many=True)

        # Get customer's payments
        payments = Payment.objects.filter(customer=customer).order_by("-created_at")
        payments_serializer = PaymentSerializer(payments, many=True)

        data = serializer.data
        data["orders"] = orders_serializer.data
        data["payments"] = payments_serializer.data

        return Response(data)


class CustomerDueOrdersView(OrgScopedQuerySetMixin, ListAPIView):
    """Get all due orders for a specific customer"""

    serializer_class = CheckoutOrderSerializer

    def get_queryset(self):
        customer_id = self.kwargs["customer_id"]
        return CheckoutOrder.objects.filter(
            customer_id=customer_id, status__in=["pending", "partially_paid"]
        ).order_by("-created_at")


class PayTotalDueView(GenericAPIView):
    """
    Make a single payment to cover a customer's total outstanding due.
    The payment is applied to the oldest due orders first.
    """

    serializer_class = PayTotalDueSerializer

    def post(self, request, *args, **kwargs):
        customer_id = self.kwargs.get("customer_id")
        try:
            customer = CustomerDetails.objects.get(id=customer_id)
        except CustomerDetails.DoesNotExist:
            return Response(
                {"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save(customer=customer)

        return Response(result, status=status.HTTP_200_OK)
