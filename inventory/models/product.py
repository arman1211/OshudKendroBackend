from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib import admin

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class GenericName(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        indexes = [
            GinIndex(fields=['name'], name='genericname_name_gin_trgm', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return self.name


class Medicine(models.Model):
    name = models.CharField(max_length=150)
    generic_name = models.ForeignKey(GenericName, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, null=True, blank=True
    )
    dosage = models.CharField(max_length=50)
    brand = models.CharField(max_length=80, blank=True, null=True)
    dosage_form = models.CharField(max_length=100, null=True, blank=True)
    strips_per_box = models.PositiveIntegerField(default=0)
    pieces_per_strip = models.PositiveIntegerField(default=0)
    pieces_per_box = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Medicine"
        verbose_name_plural = "Medicines"
        ordering = ["name"]
        indexes = [
            GinIndex(fields=['name'], name='medicine_name_gin_trgm', opclasses=['gin_trgm_ops']),
            models.Index(fields=["generic_name"]),
        ]

    def __str__(self):
        return self.name

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "dosage_form",
        "brand",
        "category",
        "strips_per_box",
        "pieces_per_strip",
        "pieces_per_box",
    ]
    search_fields = ["name", "category__name"]
    list_filter = ["dosage_form", "brand", "generic_name", "category", "created_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(GenericName)
class GenericNameAdmin(admin.ModelAdmin):
    list_display = ["name"]
