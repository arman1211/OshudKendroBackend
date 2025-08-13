from django.db import models, transaction
from django.contrib import admin
from users.models.organization import Organization
from inventory.models.product import Medicine
from inventory.models.stockpile import Inventory
from users.models.user import User
from ..models.customer_details import CustomerDetails
from decimal import Decimal


class StatusChoice(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"


class CheckoutOrder(models.Model):
    pharmacy_shop = models.ForeignKey(Organization, on_delete=models.CASCADE)
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        CustomerDetails,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkout_orders",
    )

    # Pricing fields
    checkout_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status and discount
    status = models.CharField(
        max_length=20, choices=StatusChoice.choices, default=StatusChoice.PENDING
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=0
    )

    # Legacy fields (keep for backward compatibility, but use customer FK instead)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_contact = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_total_price(self):
        """Recalculate the total price based on all related Order items"""
        total = self.items.aggregate(models.Sum("total_price"))["total_price__sum"] or 0
        self.checkout_price = total
        self.due_amount = Decimal(total) - self.paid_amount
        self.save()

    def update_status(self):
        """Update order status based on payment"""
        if self.due_amount <= 0:
            self.status = StatusChoice.COMPLETED
        elif self.paid_amount > 0:
            self.status = StatusChoice.PARTIALLY_PAID
        else:
            self.status = StatusChoice.PENDING
        self.save()

    def __str__(self):
        return f"Order {self.id} by {self.employee.email}"

    def get_orders(self):
        return [
            {
                "id": order.id,
                "batch": order.batch.batch_number if order.batch else None,
                "inventory_id": order.inventory.id if order.inventory else None,
                "medicine_name": (
                    order.inventory.medicine.name if order.inventory.medicine else None
                ),
                "pieces_per_strip": order.inventory.medicine.pieces_per_strip,
                "strips_per_box": order.inventory.medicine.strips_per_box,
                "quantity": order.quantity,
                "price_per_unit": float(order.price_per_unit),
                "discount": float(order.discount),
                "total_price": float(order.total_price),
                "created_at": order.created_at.isoformat(),
            }
            for order in self.items.all()
        ]


@admin.register(CheckoutOrder)
class CheckoutOrderAdmin(admin.ModelAdmin):
    list_display = ["pharmacy_shop", "employee", "status", "checkout_price"]
