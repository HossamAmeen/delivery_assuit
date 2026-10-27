from django.urls import path

from .staff import (
    ClientDetailView,
    ClientListView,
    DriverDetailView,
    DriverListView,
    TraderDetailView,
    TraderListView,
)
from .views import DashboardView, DriverPerformanceView

urlpatterns = [
    path(
        "drivers/performance/",
        DriverPerformanceView.as_view(),
        name="staff-driver-performance",
    ),
    path("dashboard/", DashboardView.as_view(), name="staff-dashboard"),
    path("drivers/", DriverListView.as_view(), name="staff-driver-list"),
    path("drivers/<int:pk>/", DriverDetailView.as_view(), name="staff-driver-detail"),
    path("traders/", TraderListView.as_view(), name="staff-trader-list"),
    path("traders/<int:pk>/", TraderDetailView.as_view(), name="staff-trader-detail"),
    path("clients/", ClientListView.as_view(), name="staff-client-list"),
    path("clients/<int:pk>/", ClientDetailView.as_view(), name="staff-client-detail"),
]
