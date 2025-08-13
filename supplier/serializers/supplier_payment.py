from rest_framework import serializers
from ..models.supplier_payment import SupplierPaymentRecord


class SupplierPaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPaymentRecord
        fields = ["id", "supplier", "amount", "payment_date", "notes"]
