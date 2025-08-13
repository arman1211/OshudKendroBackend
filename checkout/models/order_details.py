from django.db import models, transaction
from django.contrib import admin
from users.models.organization import Organization
from inventory.models.product import Medicine
from ..models.order import Order
from ..models.checkout_order import CheckoutOrder
from users.models.user import User


class OrderDetails(models.Model):
    pharmacy_shop = models.ForeignKey(Organization, on_delete=models.CASCADE)
    checkout = models.ForeignKey(
        CheckoutOrder, on_delete=models.CASCADE, null=True, blank=True
    )
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Order {self.id}, {self.pharmacy_shop.name} by {self.employee.first_name}"
        )


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ["pharmacy_shop", "employee", "checkout"]
