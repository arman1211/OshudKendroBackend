from rest_framework import serializers


class SalesAndProfitDashboardSerializer(serializers.Serializer):
    total_order = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    profit_without_dues = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_sales = serializers.DecimalField(max_digits=15, decimal_places=2)


class DuesDashboardSerializer(serializers.Serializer):
    total_dues = serializers.DecimalField(max_digits=15, decimal_places=2)
    dues_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    customers_with_dues = serializers.IntegerField()


class SupplierDashboardSerializer(serializers.Serializer):
    total_suppliers = serializers.IntegerField()
    total_orders_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_dues = serializers.DecimalField(max_digits=15, decimal_places=2)
    orders_with_due = serializers.IntegerField()
