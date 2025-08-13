from rest_framework import serializers
from inventory.models import Batch
from datetime import timedelta
from django.utils import timezone


class BatchSerializer(serializers.ModelSerializer):
    stock_alert_qty = serializers.IntegerField(
        source="inventory.stock_alert_qty", read_only=True
    )
    buying_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    selling_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    strips_per_box = serializers.IntegerField(
        source="inventory.medicine.strips_per_box", read_only=True
    )
    pieces_per_strip = serializers.IntegerField(
        source="inventory.medicine.pieces_per_strip", read_only=True
    )
    pieces_per_box = serializers.IntegerField(
        source="inventory.medicine.pieces_per_box", read_only=True
    )

    class Meta:
        model = Batch
        fields = "__all__"
        write_only_fields = ["batch_number", "inventory"]
        extra_fields = ["stock_alert_qty", "strips_per_box", "strips_per_box"]


class InventoryBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = [
            "id",
            "batch_number",
            "selling_price",
            "buying_price",
            "quantity",
            "expiry_date",
        ]


class BatchAlertSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source="inventory.medicine.name", read_only=True)
    generic_name = serializers.CharField(
        source="inventory.medicine.generic_name.name", read_only=True
    )
    brand = serializers.CharField(source="inventory.medicine.brand", read_only=True)
    dosage = serializers.CharField(source="inventory.medicine.dosage", read_only=True)

    quantity = serializers.IntegerField(source="inventory.quantity", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Batch

        fields = [
            "id",
            "name",
            "generic_name",
            "brand",
            "dosage",
            "quantity",
            "expiry_date",
            "status",
            "batch_number",
            "updated_at",
        ]

    def get_status(self, obj):
        alert_type = self.context["request"].query_params.get("alert_type")
        today = timezone.now().date()

        if alert_type == "stock":
            return "Stock Out" if obj.inventory.quantity == 0 else "Low Stock"

        if alert_type == "expiry":
            return "Expired" if obj.expiry_date < today else "Expiring Soon"

        return None
