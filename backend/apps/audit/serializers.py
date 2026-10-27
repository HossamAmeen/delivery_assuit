from rest_framework import serializers

from .models import AuditEntry


class AuditEntrySerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = AuditEntry
        fields = (
            "id",
            "action",
            "actor",
            "target_type",
            "target_id",
            "detail",
            "created_at",
        )

    def get_actor(self, obj):
        if obj.actor_id is None:
            return None
        return {"id": obj.actor_id, "full_name": obj.actor.full_name}
