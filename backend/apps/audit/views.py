from typing import ClassVar

import django_filters
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView

from apps.users.permissions import IsAdminOrManager

from .models import AuditEntry
from .serializers import AuditEntrySerializer


class AuditFilter(django_filters.FilterSet):
    action = django_filters.CharFilter(field_name="action")
    actor = django_filters.NumberFilter(field_name="actor_id")
    target_type = django_filters.CharFilter(field_name="target_type")
    target_id = django_filters.NumberFilter(field_name="target_id")

    class Meta:
        model = AuditEntry
        fields = ("action", "actor", "target_type", "target_id")


class AuditListView(ListAPIView):
    """Read only. There is no create, edit, or delete endpoint."""

    permission_classes: ClassVar[list] = [IsAdminOrManager]
    serializer_class = AuditEntrySerializer
    filterset_class = AuditFilter
    queryset = AuditEntry.objects.select_related("actor")

    @extend_schema(tags=["staff"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
