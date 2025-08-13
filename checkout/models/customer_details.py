from django.db import models
from django.contrib import admin
from users.models import Organization


class CustomerDetails(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    contact = models.CharField(max_length=100, null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="customers",
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("name", "contact")

    def __str__(self):
        return f"{self.name} - {self.contact}"

    @property
    def total_due_amount(self):
        """Calculate total due amount for this customer"""
        return (
            self.checkout_orders.all().aggregate(total=models.Sum("due_amount"))[
                "total"
            ]
            or 0
        )

    @property
    def total_paid_amount(self):
        """Calculate total paid amount for this customer"""
        return self.payments.aggregate(total=models.Sum("amount"))["total"] or 0


@admin.register(CustomerDetails)
class CustomerDetailsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "contact")
