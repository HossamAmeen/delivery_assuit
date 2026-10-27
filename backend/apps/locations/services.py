from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from .models import Location, SavedAddress

MAX_LOCATIONS = 50
MAX_ADDRESSES = 20


def _too_many(limit):
    raise ValidationError(
        {"non_field_errors": [_("You can keep at most %(n)d entries.") % {"n": limit}]}
    )


def _promote_default(owner, exclude_id=None):
    """Make the oldest live pickup location the default when none is."""
    live = Location.objects.filter(owner=owner, is_pickup=True)
    if live.filter(is_default_pickup=True).exists():
        return
    first = live.exclude(pk=exclude_id).order_by("id").first()
    if first:
        Location.objects.filter(pk=first.pk).update(is_default_pickup=True)


@transaction.atomic
def create_location(owner, **data) -> Location:
    # Lock the owner's rows so two requests cannot both pass the limit or the default check.
    rows = list(Location.objects.select_for_update().filter(owner=owner))
    if len(rows) >= MAX_LOCATIONS:
        _too_many(MAX_LOCATIONS)
    is_pickup = data.get("is_pickup", True)
    has_default = any(r.is_default_pickup for r in rows)
    default = is_pickup and (bool(data.get("is_default_pickup")) or not has_default)
    if default and has_default:
        Location.objects.filter(owner=owner).update(is_default_pickup=False)
    data["is_default_pickup"] = default
    return Location.objects.create(owner=owner, **data)


@transaction.atomic
def update_location(location, **data) -> Location:
    owner = location.owner
    list(Location.objects.select_for_update().filter(owner=owner))
    if data.get("is_default_pickup"):
        Location.objects.filter(owner=owner).exclude(pk=location.pk).update(
            is_default_pickup=False
        )
    if data.get("is_pickup") is False:
        data["is_default_pickup"] = False
    for key, value in data.items():
        setattr(location, key, value)
    location.save()
    _promote_default(owner)
    location.refresh_from_db()
    return location


@transaction.atomic
def delete_location(location) -> None:
    owner = location.owner
    list(Location.objects.select_for_update().filter(owner=owner))
    location.is_default_pickup = False
    location.save(update_fields=["is_default_pickup", "modified_at"])
    location.soft_delete()
    _promote_default(owner)


@transaction.atomic
def create_address(owner, **data) -> SavedAddress:
    list(SavedAddress.objects.select_for_update().filter(owner=owner))
    if SavedAddress.objects.filter(owner=owner).count() >= MAX_ADDRESSES:
        _too_many(MAX_ADDRESSES)
    return SavedAddress.objects.create(owner=owner, **data)
