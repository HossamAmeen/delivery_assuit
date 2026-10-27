import django_filters

from .models import Shop, ShopItem


class ShopItemFilter(django_filters.FilterSet):
    hidden = django_filters.BooleanFilter(field_name="is_hidden")
    search = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = ShopItem
        fields = ("hidden", "search")


class PublicShopFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Shop
        fields = ("search",)
