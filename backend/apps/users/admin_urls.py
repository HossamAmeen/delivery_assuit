from django.urls import path

from .admin_views import (
    ActivateView,
    ApproveView,
    DeactivateView,
    RejectView,
    UserDetailView,
    UserListView,
)

urlpatterns = [
    path("", UserListView.as_view(), name="user-list"),
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("<int:pk>/approve/", ApproveView.as_view(), name="user-approve"),
    path("<int:pk>/reject/", RejectView.as_view(), name="user-reject"),
    path("<int:pk>/activate/", ActivateView.as_view(), name="user-activate"),
    path("<int:pk>/deactivate/", DeactivateView.as_view(), name="user-deactivate"),
]
