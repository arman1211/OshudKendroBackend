from ..models.supplier import Supplier
from rest_framework import serializers


class SupplierSerializer(serializers.ModelSerializer):
    total_orders = serializers.ReadOnlyField()
    total_payments = serializers.ReadOnlyField()
    total_due = serializers.ReadOnlyField()

    class Meta:
        model = Supplier
        fields = "__all__"
