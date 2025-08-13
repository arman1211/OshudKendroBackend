from django.db import models, transaction
from rest_framework import serializers
from ..models.customer_details import CustomerDetails
from ..models.checkout_order import StatusChoice
from ..models.checkout_payment import Payment


class CustomerDetailsSerializer(serializers.ModelSerializer):
    total_due_amount = serializers.ReadOnlyField()
    total_paid_amount = serializers.ReadOnlyField()

    class Meta:
        model = CustomerDetails
        fields = ["id", "name", "contact", "total_due_amount", "total_paid_amount"]


class PayTotalDueSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(
        choices=[
            ("cash", "Cash"),
            ("card", "Card"),
            ("mobile", "Mobile Banking"),
            ("bank", "Bank Transfer"),
        ],
        default="cash",
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be positive.")
        return value

    def save(self, customer):
        validated_data = self.validated_data
        payment_amount = validated_data["amount"]

        due_orders = customer.checkout_orders.filter(
            status__in=[StatusChoice.PENDING, StatusChoice.PARTIALLY_PAID]
        ).order_by("created_at")

        if not due_orders.exists():
            raise serializers.ValidationError("This customer has no outstanding dues.")

        total_due = sum(order.due_amount for order in due_orders)
        if payment_amount > total_due:
            raise serializers.ValidationError(
                f"Payment amount {payment_amount} exceeds the total due of {total_due}."
            )

        remaining_payment = payment_amount

        try:
            with transaction.atomic():
                for order in due_orders:
                    if remaining_payment <= 0:
                        break

                    payment_for_this_order = min(remaining_payment, order.due_amount)

                    Payment.objects.create(
                        checkout_order=order,
                        customer=customer,
                        amount=payment_for_this_order,
                        payment_method=validated_data["payment_method"],
                        notes=validated_data.get("notes", "Payment towards total due."),
                    )

                    remaining_payment -= payment_for_this_order

                customer.refresh_from_db()
                print(
                    f"Customer total due amount after payment: {customer.total_due_amount}, paid amount: {(total_due - payment_amount)}"
                )
                if customer.total_due_amount != (total_due - payment_amount):
                    raise Exception(
                        "Payment distribution failed. Rolling back transaction."
                    )

        except Exception as e:
            raise serializers.ValidationError(f"An error occurred: {str(e)}")

        return {
            "message": f"Payment of {payment_amount} applied successfully.",
            "remaining_due": customer.total_due_amount,
        }
