from django.db import transaction
from rest_framework import viewsets
from ..models.order import Order
from ..serializers.order import OrderSerializer
from rest_framework.response import Response
from rest_framework import status

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class=None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        
        order = self.get_object()
        checkout = order.checkout
        response = super().destroy(request, *args, **kwargs)
        if checkout:
            checkout.update_total_price()
        return response