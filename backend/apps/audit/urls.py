from django.urls import path

from .views import AuditListView

urlpatterns = [
    path("audit/", AuditListView.as_view(), name="staff-audit"),
]
