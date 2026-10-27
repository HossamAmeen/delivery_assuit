PY ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)

.PHONY: install install-dev run migrate makemigrations test coverage check lint format shell collectstatic test-rate-limit create-admin seed-demo compilemessages

install:
	$(PY) -m pip install -r requirements/production.txt

install-dev:
	$(PY) -m pip install -r requirements/development.txt

run:
	$(PY) manage.py migrate --noinput
	$(PY) manage.py runserver

migrate:
	$(PY) manage.py migrate

makemigrations:
	$(PY) manage.py makemigrations

test:
	$(PY) -m pytest
	$(PY) -m pytest -k "throttle or rate_limit" --no-header -q || [ $$? -eq 5 ]

coverage:
	$(PY) -m pytest --cov=. --cov-report=term-missing

check:
	$(PY) manage.py check
	$(PY) manage.py makemigrations --check --dry-run

lint:
	$(PY) -m ruff check .

format:
	$(PY) -m ruff format .

shell:
	$(PY) manage.py shell

collectstatic:
	$(PY) manage.py collectstatic --noinput

test-rate-limit:
	$(PY) -m pytest -k "throttle or rate_limit"

# Reads ADMIN_USERNAME / ADMIN_PASSWORD from the environment, else prompts.
create-admin:
	$(PY) manage.py create_admin

# Idempotent demo data. Needs DEMO_PASSWORD; refuses when DEBUG=False (add --force manually).
seed-demo:
	$(PY) manage.py seed_demo

# Compile locale/*/LC_MESSAGES/django.po. Uses msgfmt when installed, else the Python fallback.
compilemessages:
	@if command -v msgfmt >/dev/null 2>&1; then $(PY) manage.py compilemessages; else $(PY) scripts/compile_messages.py locale; fi
