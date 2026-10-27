"""Driver execution: the next step of an assigned order (BL-032)."""

from . import lifecycle
from .models import Order

S = Order.Status

# current status -> (next status, name the frontend uses for the button)
NEXT = {
    S.ASSIGNED: (S.PICKED_UP, "pick_up"),
    S.PICKED_UP: (S.IN_DELIVERY, "start_delivery"),
    S.IN_DELIVERY: (S.DELIVERED, "deliver"),
}


def next_action(order):
    step = NEXT.get(order.status)
    return step[1] if step else None


def advance(order, actor) -> Order:
    """Move to the next step. The status is chosen here, so a step cannot be skipped."""
    step = NEXT.get(order.status)
    if step is None:
        # Routed through the lifecycle so the refusal text is the same everywhere.
        return lifecycle.transition(order, S.DELIVERED, actor)
    return lifecycle.transition(order, step[0], actor)
