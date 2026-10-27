import django_filters

from .assign import ACTIVE
from .models import Order


class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.Status.choices)
    scope = django_filters.ChoiceFilter(
        choices=(("active", "active"), ("history", "history")), method="filter_scope"
    )

    created_from = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_to = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )
    search = django_filters.CharFilter(field_name="reference", lookup_expr="icontains")

    class Meta:
        model = Order
        fields = ("status", "scope", "created_from", "created_to", "search")

    def filter_scope(self, queryset, name, value):
        if value == "active":
            # Newest assignment first (BL-029).
            return queryset.filter(status__in=ACTIVE).order_by("-assigned_at", "-id")
        return queryset.filter(
            status__in=(Order.Status.DELIVERED, Order.Status.CANCELLED)
        ).order_by("-id")


class DriverFilter(django_filters.FilterSet):
    available = django_filters.BooleanFilter(method="filter_available")

    def filter_available(self, queryset, name, value):
        # "available=true" hides busy drivers; "false" shows only the busy ones.
        return queryset.filter(has_active_order=not value)
