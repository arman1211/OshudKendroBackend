from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models.order_details import OrderDetails
from ..serializers.orderdetails import OrderDetailsSerializer

class OrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API View to fetch the checkout order history"""
    queryset = OrderDetails.objects.all().order_by("-created_at")
    serializer_class = OrderDetailsSerializer
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     # Fetch checkout history only for the logged-in user's pharmacy shop
    #     return self.queryset.filter(pharmacy_shop=self.request.user.pharmacy_shop)
    def get_queryset(self):
        pharmacy_shop = getattr(self.request.user, "pharmacy_shop", None)
        if pharmacy_shop:
            return self.queryset.filter(pharmacy_shop=pharmacy_shop)
        return self.queryset.none()  # কিছুই না দিলে খালি queryset দিবে

