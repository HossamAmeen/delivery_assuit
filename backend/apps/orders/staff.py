"""Staff management lists and details for drivers, traders and clients (BL-056, BL-057, BL-058)."""

import re
from typing import ClassVar

import django_filters
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from apps.locations.models import Location
from apps.locations.serializers import LocationSerializer
from apps.shops.models import Shop, ShopItem
from apps.shops.serializers import ShopItemSerializer, ShopSerializer
from apps.users.admin_serializers import ManagedUserSerializer
from apps.users.models import User
from apps.users.permissions import IsAdminOrManager
from apps.users.phone import normalize_phone
from common.responses import success_response

from .models import Order
from .serializers import OrderSerializer
from .visibility import visible_orders

_DIGITS_ONLY = re.compile(r"[\d\s+\-()]+")
RECENT = 20


class StaffUserFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=User.Status.choices)
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = User
        fields = ("status", "search")

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        query = Q(full_name__icontains=value)
        # Only digit-like text can match a phone ("driver1" must not match "1").
        if _DIGITS_ONLY.fullmatch(value):
            digits = normalize_phone(value)
            if digits:
                query |= Q(phone__contains=digits)
        return queryset.filter(query)


class _Row(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "phone", "status")


class DriverRow(_Row):
    delivered_orders = serializers.IntegerField(read_only=True)

    class Meta(_Row.Meta):
        fields = (*_Row.Meta.fields, "delivered_orders")


class TraderRow(_Row):
    shop_name = serializers.SerializerMethodField()
    shop_phone = serializers.SerializerMethodField()
    orders = serializers.IntegerField(source="order_count", read_only=True)

    class Meta(_Row.Meta):
        fields = (*_Row.Meta.fields, "shop_name", "shop_phone", "orders")

    def _shop(self, obj):
        return getattr(obj, "shop", None) if hasattr(obj, "shop") else None

    def get_shop_name(self, obj) -> str:
        shop = self._shop(obj)
        return shop.name if shop else ""

    def get_shop_phone(self, obj) -> str:
        shop = self._shop(obj)
        return shop.phone if shop else ""


class ClientRow(_Row):
    orders = serializers.IntegerField(source="order_count", read_only=True)

    class Meta(_Row.Meta):
        fields = (*_Row.Meta.fields, "orders")


class _StaffMixin:
    role = None
    permission_classes: ClassVar[list] = [IsAdminOrManager]

    def users(self):
        return User.objects.filter(role=self.role)


class _StaffList(_StaffMixin, ListAPIView):
    filterset_class = StaffUserFilter

    @extend_schema(tags=["staff"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DriverListView(_StaffList):
    role = User.Role.DRIVER
    serializer_class = DriverRow

    def get_queryset(self):
        return (
            self.users()
            .annotate(
                delivered_orders=Count(
                    "driver_orders",
                    filter=Q(driver_orders__status=Order.Status.DELIVERED),
                    distinct=True,
                )
            )
            .order_by("-id")
        )


class TraderListView(_StaffList):
    role = User.Role.TRADER
    serializer_class = TraderRow

    def get_queryset(self):
        return (
            self.users()
            .select_related("shop")
            .annotate(order_count=Count("shop__orders", distinct=True))
            .order_by("-id")
        )


class ClientListView(_StaffList):
    role = User.Role.CLIENT
    serializer_class = ClientRow

    def get_queryset(self):
        return (
            self.users()
            .annotate(order_count=Count("orders", distinct=True))
            .order_by("-id")
        )


class _StaffDetail(_StaffMixin, APIView):
    def orders_of(self, user):
        raise NotImplementedError

    def extra(self, user) -> dict:
        return {}

    @extend_schema(tags=["staff"])
    def get(self, request, pk):
        user = get_object_or_404(self.users(), pk=pk)
        orders = self.orders_of(user)
        recent = visible_orders(request.user).filter(pk__in=orders.values("pk"))[
            :RECENT
        ]
        data = {
            "user": ManagedUserSerializer(user).data,
            "orders_total": orders.count(),
            "recent_orders": OrderSerializer(
                recent, many=True, context={"request": request}
            ).data,
            **self.extra(user),
        }
        return success_response(data)


class DriverDetailView(_StaffDetail):
    role = User.Role.DRIVER

    def orders_of(self, user):
        return Order.objects.filter(driver=user)

    def extra(self, user):
        mine = Order.objects.filter(driver=user)
        active = mine.filter(
            status__in=("assigned", "picked_up", "in_delivery")
        ).first()
        return {
            "delivered_orders": mine.filter(status=Order.Status.DELIVERED).count(),
            "cancelled_orders": mine.filter(status=Order.Status.CANCELLED).count(),
            "active_order_reference": active.reference if active else None,
        }


class TraderDetailView(_StaffDetail):
    role = User.Role.TRADER

    def orders_of(self, user):
        return Order.objects.filter(shop__owner=user)

    def extra(self, user):
        shop = Shop.objects.filter(owner=user).first()
        items = ShopItem.objects.filter(shop=shop) if shop else ShopItem.objects.none()
        return {
            "shop": ShopSerializer(shop).data if shop else None,
            "locations": LocationSerializer(
                Location.objects.filter(owner=user), many=True
            ).data,
            "items": ShopItemSerializer(items, many=True).data,
        }


class ClientDetailView(_StaffDetail):
    role = User.Role.CLIENT

    def orders_of(self, user):
        return Order.objects.filter(client=user)
