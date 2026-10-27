from typing import ClassVar

import django_filters
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from apps.users.permissions import IsOperational
from common.responses import success_response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationFilter(django_filters.FilterSet):
    unread = django_filters.BooleanFilter(method="filter_unread")

    class Meta:
        model = Notification
        fields = ("unread",)

    def filter_unread(self, queryset, name, value):
        return queryset.filter(read_at__isnull=bool(value))


class NotificationListView(ListAPIView):
    permission_classes: ClassVar[list] = [IsOperational]
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @extend_schema(tags=["notifications"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UnreadCountView(APIView):
    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(tags=["notifications"])
    def get(self, request):
        count = Notification.objects.filter(
            user=request.user, read_at__isnull=True
        ).count()
        return success_response({"count": count})


class MarkReadView(APIView):
    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(request=None, tags=["notifications"])
    def post(self, request, pk):
        # Someone else's notification is a 404.
        item = get_object_or_404(Notification, pk=pk, user=request.user)
        if item.read_at is None:
            item.read_at = timezone.now()
            item.save(update_fields=["read_at"])
        return success_response({"notification": NotificationSerializer(item).data})


class ReadAllView(APIView):
    permission_classes: ClassVar[list] = [IsOperational]

    @extend_schema(request=None, tags=["notifications"])
    def post(self, request):
        marked = Notification.objects.filter(
            user=request.user, read_at__isnull=True
        ).update(read_at=timezone.now())
        return success_response({"marked": marked})
