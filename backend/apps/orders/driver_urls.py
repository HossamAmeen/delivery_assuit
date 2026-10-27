from django.urls import path

from .views import DriverListView, MyPerformanceView

urlpatterns = [
    path("", DriverListView.as_view(), name="driver-list"),
    path("me/performance/", MyPerformanceView.as_view(), name="my-performance"),
]
