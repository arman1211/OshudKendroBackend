from rest_framework import serializers
from ..models.product import Medicine, Category, GenericName
from ..models.unitmedicine import UnitPriceMedicine
from ..models.product import GenericName
from ..models.stockpile import Inventory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class GenericNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericName
        fields = "__all__"


class UnitPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitPriceMedicine
        fields = "__all__"


class MedicineSerializer(serializers.ModelSerializer):
    generic_name_display = serializers.CharField(
        source="generic_name.name", read_only=True
    )
    is_in_inventory = serializers.BooleanField(read_only=True)

    class Meta:
        model = Medicine
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        medicine = super().create(validated_data)

        if request and hasattr(request.user, "organization"):
            Inventory.objects.create(
                medicine=medicine,
                organization=request.user.organization,
                buying_price=0,
                selling_price=0,
                strips_per_box=medicine.strips_per_box,
                pieces_per_strip=medicine.pieces_per_strip,
                quantity=0,
                stock_alert_qty=0,
            )

        return medicine
