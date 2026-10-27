#!/usr/bin/env bash
# Upload backend + built frontend to the server and run ops/server/deploy.sh there.
# Used by GitHub Actions and by `make deploy`. No Docker.
#
# Required env: SSH_HOST, SSH_USER.  Optional: SSH_KEY (path), SSH_PORT, FRONTEND_DOMAIN, API_DOMAIN,
# APP_DIR, WEB_ROOT, BACKEND_PORT, ENABLE_SSL, SSL_EMAIL, SKIP_BUILD=1 (reuse frontend/dist).
set -euo pipefail
cd "$(dirname "$0")/.."

: "${SSH_HOST:?set SSH_HOST}" "${SSH_USER:?set SSH_USER}"
APP_NAME="${APP_NAME:-delivery}"
APP_DIR="${APP_DIR:-/opt/${APP_NAME}}"
WEB_ROOT="${WEB_ROOT:-/var/www/${APP_NAME}}"
FRONTEND_DOMAIN="${FRONTEND_DOMAIN:-delivery.hossam-ameen.online}"
API_DOMAIN="${API_DOMAIN:-api.delivery.hossam-ameen.online}"
ENABLE_SSL="${ENABLE_SSL:-true}"
SCHEME=http; [[ "${ENABLE_SSL}" == "true" ]] && SCHEME=https

SSH_OPTS=(-p "${SSH_PORT:-22}" -o StrictHostKeyChecking=accept-new)
[[ -n "${SSH_KEY:-}" ]] && SSH_OPTS+=(-i "${SSH_KEY}")
SSH=(ssh "${SSH_OPTS[@]}")
TARGET="${SSH_USER}@${SSH_HOST}"
RSYNC=(rsync -az --delete -e "ssh ${SSH_OPTS[*]}")

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo "==> Building frontend"
  (cd frontend && { [[ -f package-lock.json ]] && npm ci || npm install; } \
    && VITE_API_URL="${SCHEME}://${API_DOMAIN}/api/v1" npm run build)
fi
[[ -f frontend/dist/index.html ]] || { echo "frontend/dist missing" >&2; exit 1; }

echo "==> Preparing directories on ${TARGET}"
"${SSH[@]}" "${TARGET}" "sudo mkdir -p '${APP_DIR}/backend' '${WEB_ROOT}' && sudo chown -R '${SSH_USER}:' '${APP_DIR}' '${WEB_ROOT}'"

echo "==> Uploading backend"
"${RSYNC[@]}" \
  --exclude '.env' --exclude 'venv/' --exclude '.venv/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude 'media/' --exclude 'staticfiles/' --exclude '*.sqlite3' --exclude 'tests/' --exclude '.pytest_cache/' \
  backend/ "${TARGET}:${APP_DIR}/backend/"

echo "==> Uploading frontend"
"${RSYNC[@]}" frontend/dist/ "${TARGET}:${WEB_ROOT}/"

echo "==> Running server deploy"
"${SSH[@]}" "${TARGET}" env \
  APP_NAME="${APP_NAME}" APP_DIR="${APP_DIR}" WEB_ROOT="${WEB_ROOT}" \
  FRONTEND_DOMAIN="${FRONTEND_DOMAIN}" API_DOMAIN="${API_DOMAIN}" \
  BACKEND_PORT="${BACKEND_PORT:-8010}" ENABLE_SSL="${ENABLE_SSL}" \
  SSL_EMAIL="${SSL_EMAIL:-hosamameen948@gmail.com}" \
  bash -s <ops/server/deploy.sh
