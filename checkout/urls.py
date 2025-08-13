from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.order import OrderViewSet
from .views.odercheck import CheckoutOrderViewSet, CustomerStatsView
from .views.orderdetails import OrderHistoryViewSet
from .views.customer_details import (
    CustomerDetailsList,
    CustomerDetailView,
    CustomerDueOrdersView,
    CustomerListView,
    PayTotalDueView,
)
from .views.checkout_payment import MakePaymentView
from .views.dashboard import (
    SalesAndProfitDashboardApiView,
    DuesDashboardApiView,
    SupplierDashboardAPIView,
)

router = DefaultRouter()
router.register(r"Cart", OrderViewSet)
router.register(r"Checkout", CheckoutOrderViewSet, basename="checkout-order")
router.register(r"checkout-history", OrderHistoryViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("customer_details/", CustomerDetailsList.as_view()),
    path("customers/", CustomerListView.as_view(), name="customer-list"),
    path("customers-stats/", CustomerStatsView.as_view(), name="customer-stats"),
    path("customers/<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path(
        "customers/<int:customer_id>/due-orders/",
        CustomerDueOrdersView.as_view(),
        name="customer-due-orders",
    ),
    path(
        "customers/<int:customer_id>/pay-total-due/",
        PayTotalDueView.as_view(),
        name="customer-pay-total-due",
    ),
    path("make-payment/", MakePaymentView.as_view(), name="make-payment"),
    path(
        "dashboard/sales-profit/",
        SalesAndProfitDashboardApiView.as_view(),
        name="dashboard-sales",
    ),
    path(
        "dashboard/dues-report/",
        DuesDashboardApiView.as_view(),
        name="dashboard-dues",
    ),
    path(
        "dashboard/suppliers/",
        SupplierDashboardAPIView.as_view(),
        name="dashboard-suppliers",
    ),
]
