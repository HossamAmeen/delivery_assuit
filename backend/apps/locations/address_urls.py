from django.urls import path

from .views import AddressDetailView, AddressListView

urlpatterns = [
    path("", AddressListView.as_view(), name="address-list"),
    path("<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
]
