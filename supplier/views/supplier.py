from ..models.supplier import Supplier
from ..models.supplier_payment import SupplierPaymentRecord
from ..serializers.supplier_payment import SupplierPaymentRecordSerializer
from rest_framework.viewsets import ModelViewSet
from ..serializers.supplier import SupplierSerializer
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from ..serializers.supplier_order import SupplierPaymentSerializer
from django.shortcuts import get_object_or_404


class SupplierViewSet(ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    filter_backends = [SearchFilter]
    search_fields = ["name", "phone"]

    def get_queryset(self):
        user = self.request.user
        queryset = Supplier.objects.filter(organization=user.organization)
        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

    @action(detail=True, methods=["post"], url_path="pay-due")
    def pay_due(self, request, pk=None):
        """
        Pay due amount for a specific supplier
        """
        # supplier = get_object_or_404(
        #     Supplier, pk=pk, organization=request.user.organization
        # )
        supplier = self.get_object()

        serializer = SupplierPaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment_amount = serializer.validated_data["payment_amount"]
            notes = serializer.validated_data.get("notes", "")

            # Check if supplier has any due amount
            if supplier.total_due <= 0:
                return Response(
                    {"error": "This supplier has no due amount to pay"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:

                # Process payment
                payment_result = supplier.pay_due(payment_amount)

                SupplierPaymentRecord.objects.create(
                    supplier=supplier,
                    organization=request.user.organization,
                    amount=payment_amount,
                    notes=notes,
                )

                # Return success response with payment details
                return Response(
                    {
                        "message": "Payment processed successfully",
                        "supplier_id": supplier.id,
                        "supplier_name": supplier.name,
                        "payment_result": payment_result,
                    },
                    status=status.HTTP_200_OK,
                )

            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"error": "An error occurred while processing payment"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="payment-history")
    def payment_history(self, request, pk=None):
        """
        Get all payment records for a specific supplier.
        """
        supplier = self.get_object()
        payment_records = supplier.payment_records.all()
        serializer = SupplierPaymentRecordSerializer(payment_records, many=True)
        response_data = {
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "payment_history": serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="due-orders")
    def due_orders(self, request, pk=None):
        """
        Get all orders with due amounts for a specific supplier
        """
        supplier = get_object_or_404(
            Supplier, pk=pk, organization=request.user.organization
        )

        due_orders = supplier.get_orders_with_due()
        orders_data = []

        for order in due_orders:
            orders_data.append(
                {
                    "id": order.id,
                    "order_date": order.order_date,
                    "total_amount": order.total_amount,
                    "paid_amount": order.paid_amount,
                    "due_amount": order.due_amount,
                    "notes": order.notes,
                }
            )

        return Response(
            {
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "total_due": supplier.total_due,
                "orders_with_due": orders_data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="all-orders")
    def all_orders(self, request, pk=None):
        """
        Get all orders for a specific supplier, ordered by date (oldest first)
        """
        supplier = get_object_or_404(
            Supplier, pk=pk, organization=request.user.organization
        )

        all_orders = supplier.get_all_orders()
        orders_data = []

        for order in all_orders:
            orders_data.append(
                {
                    "id": order.id,
                    "order_date": order.order_date,
                    "total_amount": order.total_amount,
                    "paid_amount": order.paid_amount,
                    "due_amount": order.due_amount,
                    "notes": order.notes,
                }
            )

        return Response(
            {
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "orders": orders_data,
            },
            status=status.HTTP_200_OK,
        )
