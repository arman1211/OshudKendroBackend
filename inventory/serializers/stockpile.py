from rest_framework import serializers
from ..models.stockpile import Inventory
from ..models.product import Medicine
from inventory.serializers.medicine import MedicineSerializer
from inventory.serializers.batch import InventoryBatchSerializer
from users.models.organization import Organization


class InventorySerializer(serializers.ModelSerializer):
    medicine_detail = serializers.SerializerMethodField(read_only=True)
    batches = serializers.SerializerMethodField()
    strips_per_box = serializers.IntegerField(source="medicine.strips_per_box")
    pieces_per_strip = serializers.IntegerField(source="medicine.pieces_per_strip")
    pieces_per_box = serializers.IntegerField(source="medicine.pieces_per_box")

    class Meta:
        model = Inventory
        read_only_fields = ["selling_price", "expiry_date"]
        fields = "__all__"
        extra_fields = ["strips_per_box", "pieces_per_strip", "pieces_per_box"]

    def get_medicine_detail(self, obj):
        return MedicineSerializer(obj.medicine).data

    def get_batches(self, obj):
        batches = obj.batches.filter(quantity__gt=0).order_by("expiry_date")
        return InventoryBatchSerializer(batches, many=True).data


class InventoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ["medicine"]  # Only medicine is required in request
        extra_kwargs = {"medicine": {"required": True}}

    def validate(self, data):
        request = self.context.get("request")
        if not request or not request.user.organization:
            raise serializers.ValidationError("User organization not found")

        if Inventory.objects.filter(
            medicine=data["medicine"], organization=request.user.organization
        ).exists():
            raise serializers.ValidationError(
                "Inventory already exists for this medicine in your organization"
            )
        return data


class InventoryAlertSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="medicine.name", read_only=True)
    generic_name = serializers.CharField(
        source="medicine.generic_name.name", read_only=True
    )
    brand = serializers.CharField(source="medicine.brand", read_only=True)
    dosage = serializers.CharField(source="medicine.dosage", read_only=True)

    status = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            "id",
            "name",
            "generic_name",
            "brand",
            "dosage",
            "quantity",
            "stock_alert_qty",
            "updated_at",
            "status",
        ]

    def get_status(self, obj):
        return "Stock Out" if obj.quantity == 0 else "Low Stock"
