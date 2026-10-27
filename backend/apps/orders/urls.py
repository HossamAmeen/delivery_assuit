from django.urls import path

from .views import (
    OrderAdvanceView,
    OrderApproveView,
    OrderAssignView,
    OrderCancelView,
    OrderDetailView,
    OrderFeeView,
    OrderListView,
    OrderRatingView,
    OrderRejectView,
    OrderSummaryView,
)

urlpatterns = [
    path("", OrderListView.as_view(), name="order-list"),
    path("summary/", OrderSummaryView.as_view(), name="order-summary"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/approve/", OrderApproveView.as_view(), name="order-approve"),
    path("<int:pk>/assign/", OrderAssignView.as_view(), name="order-assign"),
    path("<int:pk>/advance/", OrderAdvanceView.as_view(), name="order-advance"),
    path("<int:pk>/fee/", OrderFeeView.as_view(), name="order-fee"),
    path("<int:pk>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
    path("<int:pk>/rating/", OrderRatingView.as_view(), name="order-rating"),
    path("<int:pk>/reject/", OrderRejectView.as_view(), name="order-reject"),
]
