"""Concrete model used only by tests (table created in a fixture, no migration)."""

from django.db import models

from common.models import BaseModel


class Widget(BaseModel):
    name = models.CharField(max_length=20, default="w")

    class Meta:
        app_label = "common"
