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

# --- Deploy to the server from this shell, no Docker. Override on the command line if needed:
#     make deploy SSH_KEY=~/.ssh/other_key
SSH_HOST ?= 35.226.179.10
SSH_USER ?= hossam
SSH_KEY  ?= $(HOME)/.ssh/google_compute_engine
export SSH_HOST SSH_USER SSH_KEY

.PHONY: deploy
deploy:
	./ops/push.sh
