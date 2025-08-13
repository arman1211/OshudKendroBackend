from django.db import models
from django.contrib import admin
from inventory.models.stockpile import Inventory


class Batch(models.Model):
    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="batches"
    )
    buying_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    batch_number = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=20, null=True)
    shelf_no = models.CharField(max_length=10, null=True, default=None)
    unit_size = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=0)
    alert_quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.batch_number


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = [
        "batch_number",
        "quantity",
        "buying_price",
        "selling_price",
        "expiry_date",
    ]
