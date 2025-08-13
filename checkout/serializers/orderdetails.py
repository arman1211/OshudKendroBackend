from rest_framework import serializers
from ..models.order import Order
from ..models.order_details import OrderDetails  # Import OrderDetails model
from inventory.models.product import Medicine

class OrderDetailsSerializer(serializers.ModelSerializer):
    
    employee = serializers.CharField(source="employee.first_name", read_only=True)
    pharmacy_shop = serializers.CharField(source="pharmacy_shop.name", read_only=True)

    class Meta:
        model = OrderDetails
        fields = ["id", "pharmacy_shop", "employee", "checkout"]

class OrderSerializer(serializers.ModelSerializer):
    details = OrderDetailsSerializer(many=True, read_only=True, source="orderdetails_set")

    class Meta:
        model = Order
        fields = ["id", "status", "created_at", "details"]
