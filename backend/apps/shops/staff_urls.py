from django.urls import path

from .views import StaffItemPriceView

urlpatterns = [
    path("items/<int:pk>/", StaffItemPriceView.as_view(), name="staff-item-price"),
]
