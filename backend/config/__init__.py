# Celery is optional (off in development). Import it only when installed and enabled.
try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:  # celery not installed (development)
    pass
