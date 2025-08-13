from rest_framework import generics, permissions
from ..models.supplier_order import SupplierOrder
from ..serializers.supplier_order import SupplierOrderSerializer
from django.db.models import Q


class SupplierOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = SupplierOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = SupplierOrder.objects.filter(organization=user.organization)

        search_term = self.request.query_params.get("q", None)

        if search_term:
            queryset = queryset.filter(
                Q(supplier__name__icontains=search_term)
                | Q(supplier__phone__icontains=search_term)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class SupplierOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return SupplierOrder.objects.filter(organization=user.organization)
