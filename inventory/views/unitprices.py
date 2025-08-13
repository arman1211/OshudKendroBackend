from rest_framework import viewsets
from ..models import UnitPriceMedicine
from ..serializers import UnitPriceSerializer

class UnitPriceViewSet(viewsets.ModelViewSet):
    queryset = UnitPriceMedicine.objects.all()
    serializer_class = UnitPriceSerializer
    pagination_class=None
