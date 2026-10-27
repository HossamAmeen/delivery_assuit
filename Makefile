COMPOSE ?= docker compose

.PHONY: docker-local docker-down docker-logs docker-test docker-create-admin docker-seed docker-reset

# Build and start db, backend and frontend.
docker-local:
	$(COMPOSE) up --build

docker-down:
	$(COMPOSE) down

docker-logs:
	$(COMPOSE) logs -f

# Run the test suites inside the containers.
docker-test:
	$(COMPOSE) run --rm --no-deps backend python -m pytest
	$(COMPOSE) run --rm --no-deps frontend npm test

# Needs ADMIN_USERNAME and ADMIN_PASSWORD in .env.
docker-create-admin:
	$(COMPOSE) exec backend python manage.py create_admin

# Needs DEMO_PASSWORD in .env.
docker-seed:
	$(COMPOSE) exec backend python manage.py seed_demo

# DANGER: removes containers AND the database volume.
docker-reset:
	$(COMPOSE) down -v

# --- Deploy to the server without Docker (needs SSH_HOST and SSH_USER; optional SSH_KEY) ---
.PHONY: deploy
deploy:
	./ops/push.sh
