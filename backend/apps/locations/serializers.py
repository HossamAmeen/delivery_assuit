from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Location, SavedAddress

COORDINATE_FIELDS = {
    "latitude": {
        "max_digits": 8,
        "decimal_places": 6,
        "min_value": -90,
        "max_value": 90,
    },
    "longitude": {
        "max_digits": 9,
        "decimal_places": 6,
        "min_value": -180,
        "max_value": 180,
    },
}


class PlaceSerializer(serializers.ModelSerializer):
    """Shared place rules: trimmed name and address, coordinates come as a pair."""

    name = serializers.CharField(min_length=2, max_length=100)
    address = serializers.CharField(min_length=3, max_length=500)
    latitude = serializers.DecimalField(
        **COORDINATE_FIELDS["latitude"],
        coerce_to_string=False,
        required=False,
        allow_null=True,
    )
    longitude = serializers.DecimalField(
        **COORDINATE_FIELDS["longitude"],
        coerce_to_string=False,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        merged = {
            k: attrs[k] if k in attrs else getattr(self.instance, k, None)
            for k in ("latitude", "longitude")
        }
        missing = {}
        if merged["latitude"] is None and merged["longitude"] is not None:
            missing["latitude"] = [_("Latitude is required with longitude.")]
        if merged["longitude"] is None and merged["latitude"] is not None:
            missing["longitude"] = [_("Longitude is required with latitude.")]
        if missing:
            raise serializers.ValidationError(missing)
        return attrs


class LocationSerializer(PlaceSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "is_pickup",
            "is_delivery",
            "is_default_pickup",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        get = lambda k, d: attrs.get(k, getattr(self.instance, k, d))
        is_pickup, is_delivery = get("is_pickup", True), get("is_delivery", False)
        if not is_pickup and not is_delivery:
            raise serializers.ValidationError(
                {"is_pickup": [_("Choose pickup, delivery, or both.")]}
            )
        if attrs.get("is_default_pickup") and not is_pickup:
            raise serializers.ValidationError(
                {"is_default_pickup": [_("The default pickup must allow pickup.")]}
            )
        return attrs


class SavedAddressSerializer(PlaceSerializer):
    class Meta:
        model = SavedAddress
        fields = ("id", "name", "address", "latitude", "longitude", "created_at")
        read_only_fields = ("id", "created_at")
