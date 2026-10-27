from django.urls import path

from .views import HealthView, ReadyView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("health/ready/", ReadyView.as_view(), name="health-ready"),
]
