"""Rating the driver of a delivered order (BL-061, BL-051)."""

from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit import services as audit
from apps.users.models import User

from .models import Order, OrderRating


class RatingSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=500)


@transaction.atomic
def rate(order, actor, score, comment="") -> OrderRating:
    if actor.role != User.Role.CLIENT or order.client_id != actor.pk:
        raise PermissionDenied(_("Only the client of the order can rate it."))
    locked = Order.all_objects.select_for_update().get(pk=order.pk)
    if locked.status != Order.Status.DELIVERED or locked.driver_id is None:
        raise ValidationError({"status": [_("Only a delivered order can be rated.")]})
    if OrderRating.objects.filter(order=locked).exists():
        raise ValidationError({"status": [_("This order was already rated.")]})
    try:
        with transaction.atomic():
            created = OrderRating.objects.create(
                order=locked,
                client=actor,
                driver_id=locked.driver_id,
                score=score,
                comment=(comment or "").strip(),
            )
            audit.log(actor, "order.rating", "order", locked.pk, f"score {score}")
            return created
    except IntegrityError as exc:  # two taps at once: the one-to-one wins
        raise ValidationError({"status": [_("This order was already rated.")]}) from exc
