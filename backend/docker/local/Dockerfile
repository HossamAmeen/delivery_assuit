# Local development image. Build context is ./backend (see docker-compose.yml).
# No secrets are baked in: all configuration comes from the environment at run time.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.development

WORKDIR /app

# Dependencies first so this layer is cached until requirements change.
COPY requirements/ requirements/
RUN pip install -r requirements/development.txt

RUN useradd --create-home --uid 1000 app
COPY --chown=app:app . .
RUN chmod +x scripts/entrypoint.sh scripts/wait_for_db.sh
USER app

EXPOSE 8000

# Uses HEALTH_CHECK_PASSWORD from the environment; never prints it.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "scripts/healthcheck.py"]

ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
