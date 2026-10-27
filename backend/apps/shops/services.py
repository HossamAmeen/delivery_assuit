from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.locations.models import Location

from .models import Shop, ShopItem


def get_or_create_shop(user) -> Shop:
    shop, _created = Shop.objects.get_or_create(
        owner=user,
        defaults={"name": user.full_name or str(user), "phone": user.phone or ""},
    )
    return shop


def pickup_locations(shop):
    """The trader's live pickup-enabled locations, the default first (BL-020).

    Order and shop screens must use this helper, never their own query.
    """
    return Location.objects.filter(owner_id=shop.owner_id, is_pickup=True).order_by(
        "-is_default_pickup", "id"
    )


def is_shop_orderable(shop) -> bool:
    """True when clients may order from the shop: owner active, shop open, a pickup place exists.

    Pending, rejected or deactivated traders and unavailable shops are not public.
    """
    return bool(
        shop.deleted_at is None
        and shop.is_available
        and shop.owner.is_operational
        and shop.owner.role == "trader"
        and pickup_locations(shop).exists()
    )


MAX_ITEMS = 200
NAME_TAKEN = _("An item with this name already exists.")


def name_taken(shop, name, exclude_pk=None) -> bool:
    qs = ShopItem.objects.filter(shop=shop, name__iexact=name)
    return qs.exclude(pk=exclude_pk).exists() if exclude_pk else qs.exists()


@transaction.atomic
def create_item(shop, **data) -> ShopItem:
    # Lock the shop row so two requests cannot both pass the limit.
    Shop.objects.select_for_update().get(pk=shop.pk)
    if ShopItem.objects.filter(shop=shop).count() >= MAX_ITEMS:
        raise ValidationError(
            {
                "non_field_errors": [
                    _("You can keep at most %(n)d items.") % {"n": MAX_ITEMS}
                ]
            }
        )
    return _save(ShopItem(shop=shop, **data))


@transaction.atomic
def update_item(item, **data) -> ShopItem:
    for key, value in data.items():
        setattr(item, key, value)
    return _save(item)


def _save(item) -> ShopItem:
    # The unique constraint is the last line of defence against a race.
    try:
        with transaction.atomic():
            item.save()
    except IntegrityError as exc:
        raise ValidationError({"name": [NAME_TAKEN]}) from exc
    return item


def orderable_shops():
    """Queryset form of ``is_shop_orderable`` (BL-045). Keep the two in step."""
    pickups = Location.objects.filter(owner_id=OuterRef("owner_id"), is_pickup=True)
    return Shop.objects.filter(
        is_available=True,
        owner__status="active",
        owner__role="trader",
        owner__deleted_at__isnull=True,
    ).filter(Exists(pickups))
