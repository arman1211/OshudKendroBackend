from django.db import models
from django.contrib import admin
from ..models.product import Medicine

class UnitPriceMedicine(models.Model):
    medicine = models.ForeignKey(Medicine,on_delete=models.CASCADE,related_name='unit_prices')
    unit = models.CharField(max_length=50)
    item=models.PositiveIntegerField(default=1)
    unit_size = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2,editable=False)

    def save(self, *args, **kwargs):
        # Calculate the price dynamically based on medicine price and unit size
        self.price = self.medicine.price * self.unit_size
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit_size} of {self.medicine.name} ({self.unit}) - {self.price}"
    
@admin.register(UnitPriceMedicine)
class UnitPriceMedicineAdmin(admin.ModelAdmin):
    list_display=['medicine','unit','unit_size','price']