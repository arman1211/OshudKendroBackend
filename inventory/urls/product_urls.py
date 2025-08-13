from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory import views
from inventory.views.medicine import MedicineViewSet, MedicineCSVUploadView
from inventory.views.stockpile import InventoryViewSet
from inventory.views.unitprices import UnitPriceViewSet
from inventory.views import CategoryViewSet, GenericNameViewSet, MedicineCreateView

router = DefaultRouter()

router.register(r"medicines", MedicineViewSet)
router.register(r"batch", views.BatchViewSet, basename="batch")
router.register(r"generic-names", GenericNameViewSet, basename="genericname")
router.register(r"categories", CategoryViewSet, basename="categories")

urlpatterns = [
    path("", include(router.urls)),
    path("upload/", MedicineCreateView.as_view()),
    path(
        "upload-medicine-csv/",
        MedicineCSVUploadView.as_view(),
        name="upload-medicine-csv",
    ),
]
