from ..models.supplier_order import SupplierOrder
from ..models.supplier import Supplier
from ..serializers.supplier import SupplierSerializer
from rest_framework import serializers


class SupplierOrderSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source="supplier", write_only=True
    )

    class Meta:
        model = SupplierOrder
        fields = "__all__"
        read_only_fields = ["organization"]


class SupplierPaymentSerializer(serializers.Serializer):
    payment_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, help_text="Amount to pay towards supplier dues"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes for the payment record.",
    )

    def validate_payment_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than 0")
        return value
