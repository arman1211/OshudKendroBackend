from django.db import models, transaction
from django.contrib import admin
from inventory.models.product import Medicine
from inventory.models.stockpile import Inventory
from inventory.models.batch import Batch
from .checkout_order import CheckoutOrder
from django.core.validators import MinValueValidator, MaxValueValidator


class Order(models.Model):
    checkout = models.ForeignKey(
        CheckoutOrder,
        on_delete=models.CASCADE,
        related_name="items",
        null=True,
        blank=True,
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="orders", null=True
    )
    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="orders", null=True
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["checkout", "quantity", "total_price"]
