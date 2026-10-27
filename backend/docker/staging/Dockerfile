# Staging image (server): production requirements incl. gunicorn, Celery and Redis clients.
# Build context is ./backend. No secrets are baked in. Not built or run by agents yet.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.staging

WORKDIR /app

COPY requirements/ requirements/
RUN pip install -r requirements/staging.txt

RUN useradd --create-home --uid 1000 app
COPY --chown=app:app . .
RUN chmod +x scripts/entrypoint.sh scripts/wait_for_db.sh
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "scripts/healthcheck.py"]

ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
