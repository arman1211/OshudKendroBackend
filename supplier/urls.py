from django.urls import path
from .views import SupplierOrderListCreateView, SupplierOrderDetailView, SupplierViewSet
from rest_framework.routers import DefaultRouter
from django.urls import include


router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet, basename="supplier")

urlpatterns = [
    path(
        "supplier-orders/",
        SupplierOrderListCreateView.as_view(),
        name="supplier-order-list-create",
    ),
    path(
        "supplier-orders/<int:pk>/",
        SupplierOrderDetailView.as_view(),
        name="supplier-order-detail",
    ),
    path("", include(router.urls)),
]
