from django.db import models
from ..models.supplier import Supplier
from users.models.organization import Organization
from django.utils import timezone
from django.contrib import admin


class SupplierOrder(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="supplier_orders"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="supplier_orders"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2)

    order_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.supplier.name

    class Meta:
        ordering = ["-order_date"]


@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = (
        "supplier",
        "organization",
        "total_amount",
        "paid_amount",
        "due_amount",
        "order_date",
    )
