from django.db import models, transaction
from users.models.organization import Organization
from .product import Medicine
from django.contrib import admin


class Inventory(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    stock_alert_qty = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("medicine", "organization")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.medicine.name} - {self.organization.name}"


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "organization",
        "stock_alert_qty",
        "medicine",
        "quantity",
        "updated_at",
    ]
