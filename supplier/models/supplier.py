from django.db import models
from django.contrib import admin
from users.models import Organization
from django.db.models import Sum


class Supplier(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="The official name of the supplier company.",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="suppliers",
        null=True,
        help_text="Organization that owns this supplier",
    )
    address = models.TextField(
        blank=True, null=True, help_text="The physical address of the supplier."
    )
    website = models.URLField(
        blank=True, null=True, help_text="The supplier's official website."
    )
    specialization = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The area of specialization or type of products supplied.",
    )
    supplier_type = models.CharField(max_length=50, null=True, blank=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, help_text="Primary contact phone number.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def total_orders(self):
        """Calculate total amount of all orders from this supplier"""
        return self.supplier_orders.aggregate(total=Sum("total_amount"))["total"] or 0

    @property
    def total_payments(self):
        """Calculate total payments made to this supplier"""
        return self.supplier_orders.aggregate(total=Sum("paid_amount"))["total"] or 0

    @property
    def total_due(self):
        """Calculate total due amount for this supplier"""
        return self.supplier_orders.aggregate(total=Sum("due_amount"))["total"] or 0

    def get_orders_with_due(self):
        """Get all orders that have due amount, ordered by date (oldest first)"""
        return self.supplier_orders.filter(due_amount__gt=0).order_by(
            "order_date", "created_at"
        )

    def get_all_orders(self):
        """Get all orders from this supplier, ordered by date (oldest first)"""
        return self.supplier_orders.all().order_by("order_date", "created_at")

    def pay_due(self, payment_amount):
        """
        Pay due amount for this supplier, starting from oldest orders
        Returns dict with payment details
        """
        if payment_amount <= 0:
            raise ValueError("Payment amount must be greater than 0")

        total_due = self.total_due
        if payment_amount > total_due:
            raise ValueError(
                f"Payment amount ({payment_amount}) cannot exceed total due ({total_due})"
            )

        remaining_payment = payment_amount
        payment_details = []

        # Get orders with due amount, ordered by date (oldest first)
        orders_with_due = self.get_orders_with_due()

        for order in orders_with_due:
            if remaining_payment <= 0:
                break

            # Calculate how much to pay for this order
            order_due = order.due_amount
            payment_for_order = min(remaining_payment, order_due)

            # Update the order
            order.paid_amount += payment_for_order
            order.due_amount -= payment_for_order
            order.save()

            # Track payment details
            payment_details.append(
                {
                    "order_id": order.id,
                    "order_date": order.order_date,
                    "payment_amount": payment_for_order,
                    "remaining_due": order.due_amount,
                }
            )

            remaining_payment -= payment_for_order

        return {
            "total_payment": payment_amount,
            "remaining_payment": remaining_payment,
            "payment_details": payment_details,
            "new_total_due": self.total_due,
        }


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "created_at")
