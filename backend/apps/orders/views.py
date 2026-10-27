from typing import ClassVar

from django.db.models import Exists, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.permissions import IsAdminOrManager, IsClient, IsDriver, IsOperational
from common.pagination import StandardPagination
from common.responses import success_response

from . import (
    assign,
    cancel,
    create,
    dashboard,
    edit,
    execute,
    fees,
    performance,
    rating,
    review,
)
from .filters import DriverFilter, OrderFilter
from .models import Order
from .serializers import (
    ApproveSerializer,
    AssignSerializer,
    CancelSerializer,
    DriverRowSerializer,
    FeeSerializer,
    OrderDetailSerializer,
    OrderSerializer,
    RejectSerializer,
)
from .visibility import visible_orders


class OrderListView(ListAPIView):
    permission_classes: ClassVar[list] = [IsOperational]
    serializer_class = OrderSerializer
    filterset_class = OrderFilter

    def get_queryset(self):
        return visible_orders(self.request.user)

    def get_permissions(self):
        # Reading is for every role; only a client creates orders (BR-18).
        if self.request.method == "POST":
            return [IsClient()]
        return super().get_permissions()

    @extend_schema(tags=["orders"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=create.OrderCreateSerializer, responses=OrderSerializer, tags=["orders"]
    )
    def post(self, request):
        serializer = create.OrderCreateSerializer(
            data=request.data, context={"client": request.user}
        )
        serializer.is_valid(raise_exception=True)
        order = create.create_order(request.user, serializer.validated_data)
        order = visible_orders(request.user).get(pk=order.pk)
        return success_response(
            {"order": OrderSerializer(order, context={"request": request}).data},
            message=_("Your order was created."),
            status=201,
        )


class OrderDetailView(APIView):
    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(responses=OrderSerializer, tags=["orders"])
    def get(self, request, pk):
        order = get_object_or_404(visible_orders(request.user), pk=pk)
        return success_response(
            {"order": OrderDetailSerializer(order, context={"request": request}).data}
        )

    @extend_schema(
        request=edit.OrderEditSerializer, responses=OrderSerializer, tags=["orders"]
    )
    def patch(self, request, pk):
        # Not the visible set: a trader or driver who can see the order still gets 403, not 404.
        order = get_object_or_404(visible_orders(request.user), pk=pk)
        serializer = edit.OrderEditSerializer(
            data=request.data, context={"order": order, "client": order.client}
        )
        serializer.is_valid(raise_exception=True)
        edit.edit_order(order, request.user, serializer.validated_data)
        order = visible_orders(request.user).get(pk=pk)
        return success_response(
            {"order": OrderSerializer(order, context={"request": request}).data},
            message=_("Order updated."),
        )


class _ReviewView(APIView):
    permission_classes: ClassVar[list] = [IsAdminOrManager]

    def respond(self, request, order, message):
        order = visible_orders(request.user).get(pk=order.pk)
        return success_response(
            {"order": OrderSerializer(order, context={"request": request}).data},
            message=message,
        )


class OrderApproveView(_ReviewView):
    @extend_schema(
        request=ApproveSerializer, responses=OrderSerializer, tags=["orders"]
    )
    def post(self, request, pk):
        order = get_object_or_404(Order.objects, pk=pk)
        serializer = ApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.approve(
            order, request.user, serializer.validated_data.get("delivery_fee")
        )
        return self.respond(request, order, _("Order approved."))


class OrderRejectView(_ReviewView):
    @extend_schema(request=RejectSerializer, responses=OrderSerializer, tags=["orders"])
    def post(self, request, pk):
        order = get_object_or_404(Order.objects, pk=pk)
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.reject(order, request.user, serializer.validated_data["reason"].strip())
        return self.respond(request, order, _("Order rejected."))


class OrderAssignView(_ReviewView):
    @extend_schema(request=AssignSerializer, responses=OrderSerializer, tags=["orders"])
    def post(self, request, pk):
        order = get_object_or_404(Order.objects, pk=pk)
        serializer = AssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assign.assign(order, request.user, serializer.validated_data["driver"])
        return self.respond(request, order, _("Order assigned."))


class DriverListView(ListAPIView):
    """Active drivers and whether each is busy (BR-1). Admin and Manager only."""

    permission_classes: ClassVar[list] = [IsAdminOrManager]
    serializer_class = DriverRowSerializer
    filterset_class = DriverFilter

    def get_queryset(self):
        busy = Order.objects.filter(driver=OuterRef("pk"), status__in=assign.ACTIVE)
        return (
            User.objects.filter(role=User.Role.DRIVER, status=User.Status.ACTIVE)
            .annotate(
                has_active_order=Exists(busy),
                active_order_reference=Subquery(busy.values("reference")[:1]),
            )
            .order_by("full_name", "id")
        )

    @extend_schema(tags=["orders"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OrderAdvanceView(APIView):
    """The assigned driver moves the order one step (pick up, start delivery, deliver)."""

    permission_classes: ClassVar[list] = [IsDriver]

    @extend_schema(request=None, responses=OrderSerializer, tags=["orders"])
    def post(self, request, pk):
        # A driver's visible set is their own orders, so anyone else's is a 404.
        order = get_object_or_404(visible_orders(request.user), pk=pk)
        execute.advance(order, request.user)
        order = visible_orders(request.user).get(pk=pk)
        return success_response(
            {"order": OrderSerializer(order, context={"request": request}).data},
            message=_("Order updated."),
        )


class OrderFeeView(_ReviewView):
    @extend_schema(request=FeeSerializer, responses=OrderSerializer, tags=["orders"])
    def patch(self, request, pk):
        order = get_object_or_404(Order.objects, pk=pk)
        serializer = FeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fees.set_fee(order, request.user, serializer.validated_data["delivery_fee"])
        return self.respond(request, order, _("Delivery fee saved."))


class OrderCancelView(APIView):
    """The owning client (before assignment) or staff (any unfinished order)."""

    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(request=CancelSerializer, responses=OrderSerializer, tags=["orders"])
    def post(self, request, pk):
        order = get_object_or_404(visible_orders(request.user), pk=pk)
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cancel.cancel(order, request.user, serializer.validated_data.get("reason", ""))
        order = visible_orders(request.user).get(pk=pk)
        return success_response(
            {"order": OrderSerializer(order, context={"request": request}).data},
            message=_("Order cancelled."),
        )


class OrderSummaryView(APIView):
    """Counts of the orders the caller may see (BL-040). Same set as the list."""

    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(tags=["orders"])
    def get(self, request):
        S = Order.Status
        qs = visible_orders(request.user)

        def n(*statuses):
            return qs.filter(status__in=statuses).count()

        return success_response(
            {
                "total": qs.count(),
                "waiting_review": n(S.CREATED),
                "waiting_for_driver": n(S.AVAILABLE),
                "in_progress": n(S.ASSIGNED, S.PICKED_UP, S.IN_DELIVERY),
                "delivered": n(S.DELIVERED),
                "cancelled": n(S.CANCELLED),
            }
        )


class OrderRatingView(APIView):
    """The client rates the driver of a delivered order, once (BL-051)."""

    permission_classes: ClassVar[list] = [IsClient]

    @extend_schema(
        request=rating.RatingSerializer, responses=OrderSerializer, tags=["orders"]
    )
    def post(self, request, pk):
        order = get_object_or_404(visible_orders(request.user), pk=pk)
        serializer = rating.RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating.rate(
            order,
            request.user,
            serializer.validated_data["score"],
            serializer.validated_data.get("comment", ""),
        )
        order = visible_orders(request.user).get(pk=pk)
        return success_response(
            {"order": OrderSerializer(order, context={"request": request}).data},
            message=_("Thank you for your rating."),
            status=201,
        )


class MyPerformanceView(APIView):
    """A driver's own aggregates, never single ratings (BL-063)."""

    permission_classes: ClassVar[list] = [IsDriver]

    @extend_schema(tags=["orders"])
    def get(self, request):
        month = performance.parse_month(request.query_params.get("month"))
        return success_response(performance.driver_performance(request.user.pk, month))


class DriverPerformanceView(APIView):
    """Staff overview of every driver (BL-060)."""

    permission_classes: ClassVar[list] = [IsAdminOrManager]

    @extend_schema(tags=["staff"])
    def get(self, request):
        month = performance.parse_month(request.query_params.get("month"))
        ordering = request.query_params.get("ordering", "delivered")
        if ordering not in ("delivered", "rating"):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"ordering": [_("Choose delivered or rating.")]})
        drivers = list(User.objects.filter(role=User.Role.DRIVER).order_by("id"))
        rows = performance.overview(drivers, month, ordering)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(page)


class DashboardView(APIView):
    permission_classes: ClassVar[list] = [IsAdminOrManager]

    @extend_schema(tags=["staff"])
    def get(self, request):
        q = request.query_params
        return success_response(
            dashboard.build(q.get("period") or None, q.get("from"), q.get("to"))
        )
