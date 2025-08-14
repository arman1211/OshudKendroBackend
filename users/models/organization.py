from django.db import models
from django.utils.text import slugify
from django.contrib import admin
from django.conf import settings


class Organization(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    slug = models.SlugField(unique=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarded_organizations",
    )
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    is_printable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("name", "contact_number")

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_source = f"{self.name} {self.contact_number}"
            self.slug = slugify(slug_source)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __str__(self):
        return self.name


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "contact_number"]
