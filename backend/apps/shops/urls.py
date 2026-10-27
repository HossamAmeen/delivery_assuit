from django.urls import path

from .views import ItemDetailView, ItemListView, ShopView

urlpatterns = [
    path("", ShopView.as_view(), name="shop"),
    path("items/", ItemListView.as_view(), name="shop-item-list"),
    path("items/<int:pk>/", ItemDetailView.as_view(), name="shop-item-detail"),
]
