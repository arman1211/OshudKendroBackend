from django.db import models
from users.models import User, Organization


class Subscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("expired", "Expired"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status=models.CharField(max_length=10,choices=STATUS_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} Subscription by {self.user.email}"
    

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display=['organization','status','start_date','end_date','user']