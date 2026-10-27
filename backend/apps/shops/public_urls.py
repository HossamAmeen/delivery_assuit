from django.urls import path

from .views import PublicShopDetailView, PublicShopListView

urlpatterns = [
    path("", PublicShopListView.as_view(), name="public-shop-list"),
    path("<int:pk>/", PublicShopDetailView.as_view(), name="public-shop-detail"),
]
