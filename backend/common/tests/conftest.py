import pytest

# Importing the model before DB setup makes Django create its table (``common``
# has no migrations, so it is synced). It is never imported outside tests, so no
# migration is generated for it.
from common.tests.models import Widget


@pytest.fixture
def widget_db(db):
    return Widget
