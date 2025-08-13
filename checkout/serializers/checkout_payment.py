from rest_framework import serializers
from ..models.checkout_payment import Payment
from ..models.checkout_order import CheckoutOrder


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "payment_method",
            "notes",
            "created_at",
            "customer_name",
        ]
        read_only_fields = ["created_at"]


class MakePaymentSerializer(serializers.ModelSerializer):
    checkout_order_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Payment
        fields = ["checkout_order_id", "amount", "payment_method", "notes"]

    def validate_checkout_order_id(self, value):
        try:
            checkout_order = CheckoutOrder.objects.get(id=value)
            if checkout_order.due_amount <= 0:
                raise serializers.ValidationError("This order is already fully paid.")
            return value
        except CheckoutOrder.DoesNotExist:
            raise serializers.ValidationError("Checkout order not found.")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than 0.")
        return value

    def create(self, validated_data):
        checkout_order_id = validated_data.pop("checkout_order_id")
        checkout_order = CheckoutOrder.objects.get(id=checkout_order_id)

        # Validate payment amount doesn't exceed due amount
        if validated_data["amount"] > checkout_order.due_amount:
            raise serializers.ValidationError(
                f"Payment amount cannot exceed due amount of {checkout_order.due_amount}"
            )

        payment = Payment.objects.create(
            checkout_order=checkout_order,
            customer=checkout_order.customer,
            **validated_data,
        )

        return payment
