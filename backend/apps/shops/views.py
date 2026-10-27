from typing import ClassVar

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.views import APIView

from apps.users.permissions import IsAdminOrManager, IsClient, IsTrader
from common.responses import success_response

from . import services, staff
from .filters import PublicShopFilter, ShopItemFilter
from .models import ShopItem
from .serializers import (
    PublicShopDetailSerializer,
    PublicShopSerializer,
    ShopItemSerializer,
    ShopSerializer,
)


class ShopView(APIView):
    permission_classes: ClassVar[list] = [IsTrader]

    @extend_schema(responses=ShopSerializer, tags=["shop"])
    def get(self, request):
        shop = services.get_or_create_shop(request.user)
        return success_response({"shop": ShopSerializer(shop).data})

    @extend_schema(request=ShopSerializer, responses=ShopSerializer, tags=["shop"])
    def patch(self, request):
        shop = services.get_or_create_shop(request.user)
        serializer = ShopSerializer(shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            {"shop": ShopSerializer(shop).data}, message=_("Saved.")
        )


class ItemListView(ListCreateAPIView):
    """The trader's own items. Hidden ones stay in this list."""

    permission_classes: ClassVar[list] = [IsTrader]
    serializer_class = ShopItemSerializer
    filterset_class = ShopItemFilter

    def get_queryset(self):
        shop = services.get_or_create_shop(self.request.user)
        return ShopItem.objects.filter(shop=shop)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.user.is_authenticated:
            ctx["shop"] = services.get_or_create_shop(self.request.user)
        return ctx

    @extend_schema(tags=["shop"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=ShopItemSerializer, tags=["shop"])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shop = serializer.context["shop"]
        item = services.create_item(shop, **serializer.validated_data)
        return success_response(
            {"item": ShopItemSerializer(item).data}, message=_("Saved."), status=201
        )


class ItemDetailView(APIView):
    permission_classes: ClassVar[list] = [IsTrader]

    def item(self, request, pk):
        shop = services.get_or_create_shop(request.user)
        # Another shop's item is a 404, never a 403.
        return get_object_or_404(ShopItem.objects, pk=pk, shop=shop), shop

    @extend_schema(responses=ShopItemSerializer, tags=["shop"])
    def get(self, request, pk):
        item, _shop = self.item(request, pk)
        return success_response({"item": ShopItemSerializer(item).data})

    @extend_schema(request=ShopItemSerializer, tags=["shop"])
    def patch(self, request, pk):
        item, shop = self.item(request, pk)
        serializer = ShopItemSerializer(
            item, data=request.data, partial=True, context={"shop": shop}
        )
        serializer.is_valid(raise_exception=True)
        item = services.update_item(item, **serializer.validated_data)
        return success_response(
            {"item": ShopItemSerializer(item).data}, message=_("Saved.")
        )

    @extend_schema(request=None, tags=["shop"])
    def delete(self, request, pk):
        item, _shop = self.item(request, pk)
        item.soft_delete()
        return success_response({}, message=_("Deleted."))


class PublicShopListView(ListAPIView):
    """Shops a client can order from (BL-045)."""

    permission_classes: ClassVar[list] = [IsClient]
    serializer_class = PublicShopSerializer
    filterset_class = PublicShopFilter

    def get_queryset(self):
        return services.orderable_shops().order_by("name", "id")

    @extend_schema(tags=["shops"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicShopDetailView(APIView):
    permission_classes: ClassVar[list] = [IsClient]

    @extend_schema(responses=PublicShopDetailSerializer, tags=["shops"])
    def get(self, request, pk):
        # A closed or location-less shop cannot be ordered from, so it does not exist here.
        shop = get_object_or_404(services.orderable_shops(), pk=pk)
        return success_response({"shop": PublicShopDetailSerializer(shop).data})


class StaffItemPriceView(APIView):
    """Admin or Manager sets an item's price. Nobody else can (BR-17)."""

    permission_classes: ClassVar[list] = [IsAdminOrManager]

    @extend_schema(request=staff.PriceSerializer, tags=["staff"])
    def patch(self, request, pk):
        item = get_object_or_404(ShopItem.objects.select_related("shop"), pk=pk)
        serializer = staff.PriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff.set_price(item, request.user, serializer.validated_data["price"])
        data = ShopItemSerializer(item).data
        data["shop"] = {"id": item.shop_id, "name": item.shop.name}
        return success_response({"item": data}, message=_("Saved."))
