from django.db import models
from ..models.checkout_order import CheckoutOrder
from ..models.customer_details import CustomerDetails
from django.contrib import admin
from decimal import Decimal


class Payment(models.Model):
    checkout_order = models.ForeignKey(
        CheckoutOrder, on_delete=models.CASCADE, related_name="payments"
    )
    customer = models.ForeignKey(
        CustomerDetails, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("cash", "Cash"),
            ("card", "Card"),
            ("mobile", "Mobile Banking"),
            ("bank", "Bank Transfer"),
        ],
        default="cash",
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update checkout order payment status
        self.checkout_order.paid_amount = (
            self.checkout_order.payments.aggregate(total=models.Sum("amount"))["total"]
            or 0
        )
        print(f"Updated paid amount: {self.checkout_order.paid_amount}")
        self.checkout_order.due_amount = (
            Decimal(self.checkout_order.checkout_price)
            - self.checkout_order.paid_amount
        )
        self.checkout_order.update_status()

    def __str__(self):
        return f"Payment {self.amount} for Order {self.checkout_order.id}"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "checkout_order",
        "customer",
        "amount",
        "payment_method",
        "created_at",
    )
    search_fields = ("checkout_order__id", "customer__name", "payment_method")
    list_filter = ("payment_method", "created_at")
    date_hierarchy = "created_at"
