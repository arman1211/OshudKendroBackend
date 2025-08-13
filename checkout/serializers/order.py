from rest_framework import serializers
from django.db import transaction
from ..models.order import Order


class OrderSerializer(serializers.ModelSerializer):
    # medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    class Meta:
        model = Order
        fields = [
            "id",
            "checkout",
            "quantity",
            "price_per_unit",
            "total_price",
            "created_at",
        ]
        read_only_fields = ["price_per_unit", "total_price", "created_at"]

    def validate(self, data):
        # batch = data.get('batch')
        medicine = data.get("medicine")
        quantity = data.get("quantity")
        if medicine and quantity and medicine.quantity < quantity:
            raise serializers.ValidationError(
                f"Not enough stock for {medicine.name}. Available: {medicine.quantity}"
            )
        return data
