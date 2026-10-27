import re

import django_filters
from django.db.models import Q

from .models import User
from .phone import normalize_phone

_DIGITS_ONLY = re.compile(r"[\d\s+\-()]+")


class UserFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=User.Role.choices)
    status = django_filters.ChoiceFilter(choices=User.Status.choices)
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = User
        fields = ("role", "status", "search")

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        query = Q(full_name__icontains=value)
        # Only digit-like text can match a phone ("manager1" must not match "1").
        if _DIGITS_ONLY.fullmatch(value):
            digits = normalize_phone(value)
            if digits:
                query |= Q(phone__contains=digits)
        return queryset.filter(query)
