from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(read_only=True, allow_null=True)
    reference = serializers.SerializerMethodField()
    read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ("id", "kind", "order_id", "reference", "read", "created_at")

    def get_reference(self, obj):
        return obj.reference or None

    def get_read(self, obj) -> bool:
        return obj.read_at is not None
