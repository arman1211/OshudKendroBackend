from django.db import models
from django.utils import timezone
from .supplier import Supplier
from users.models.organization import Organization
from django.contrib import admin


class SupplierPaymentRecord(models.Model):
    """
    Records every individual payment made to a supplier.
    """

    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="payment_records"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="supplier_payment_records"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The amount paid in this transaction.",
    )
    payment_date = models.DateTimeField(
        default=timezone.now, help_text="The date and time the payment was made."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes for the payment (e.g., transaction ID, payment method).",
    )

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"Payment of {self.amount} to {self.supplier.name} on {self.payment_date.date()}"


@admin.register(SupplierPaymentRecord)
class SupplierPaymentRecordAdmin(admin.ModelAdmin):
    list_display = ("supplier", "amount", "payment_date", "organization")
    search_fields = ("supplier__name", "notes")
    list_filter = ("payment_date", "organization")
    date_hierarchy = "payment_date"
    ordering = ("-payment_date",)
