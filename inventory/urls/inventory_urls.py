from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.views.medicine import MedicineViewSet
from inventory.views.stockpile import InventoryViewSet
from inventory.views.unitprices import UnitPriceViewSet
from inventory.views import CategoryViewSet, GenericNameViewSet
from inventory.views.batch import MedicineAlertsView, AlertsSummaryView
from inventory import views

router = DefaultRouter()

router.register(r"stockpiles", InventoryViewSet)
router.register(r"unitprices", UnitPriceViewSet)
router.register(r"categories", CategoryViewSet, basename="category")

urlpatterns = [
    path(
        "products/batch/generate/",
        views.GenerateBatchNumberView.as_view(),
        name="generate-batch-number",
    ),
    path("batch/update/<int:batch_id>/", views.BatchPartialUpdateAPI.as_view()),
    path("alerts/", MedicineAlertsView.as_view(), name="medicine-alerts"),
    path("alerts/summary/", AlertsSummaryView.as_view(), name="alerts-summary"),
    path(
        "quantity/<int:pk>/",
        views.InventoryQuantityView.as_view(),
        name="get_inventory_quantity",
    ),
    path("", include(router.urls)),
]
