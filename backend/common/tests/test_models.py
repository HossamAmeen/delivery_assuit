import pytest

pytestmark = pytest.mark.django_db


def test_timestamps_set(widget_db):
    w = widget_db.objects.create()
    assert w.created_at and w.modified_at and w.deleted_at is None
    assert not w.is_deleted


def test_soft_delete_hides_from_default_manager(widget_db):
    w = widget_db.objects.create()
    w.soft_delete()
    assert w.is_deleted
    assert widget_db.objects.count() == 0
    assert widget_db.deleted_objects.count() == 1
    assert widget_db.all_objects.count() == 1


def test_restore(widget_db):
    w = widget_db.objects.create()
    w.soft_delete()
    w.restore()
    assert widget_db.objects.filter(pk=w.pk).exists()
    assert widget_db.deleted_objects.count() == 0


def test_queryset_bulk_soft_delete_and_restore(widget_db):
    widget_db.objects.create()
    widget_db.objects.create()
    assert widget_db.objects.all().soft_delete() == 2
    assert widget_db.objects.count() == 0
    assert widget_db.deleted_objects.all().restore() == 2
    assert widget_db.objects.count() == 2
