#!/usr/bin/env bash
# Wait for the database, apply migrations, then run the given command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/wait_for_db.sh"
# Celery worker/beat set RUN_MIGRATIONS=false so only the web container migrates.
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
    python manage.py migrate --noinput
fi

exec "$@"
