#!/usr/bin/env bash
# Wait until the database in DATABASE_URL accepts TCP connections. Never prints the URL.
# SQLite or an unset DATABASE_URL needs no waiting.
set -euo pipefail

TIMEOUT="${DB_WAIT_TIMEOUT:-60}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Waiting for the database (up to ${TIMEOUT}s)..."
for ((i = 1; i <= TIMEOUT; i++)); do
    if "${PYTHON:-python}" "${SCRIPT_DIR}/db_ready.py"; then
        echo "Database is ready."
        exit 0
    fi
    sleep 1
done

echo "Database did not become ready within ${TIMEOUT}s." >&2
exit 1
