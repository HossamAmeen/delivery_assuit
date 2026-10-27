#!/usr/bin/env bash
# Runs ON THE SERVER (Debian/Ubuntu, no Docker). Idempotent: safe for first install and every release.
#
# Expects the code to be already uploaded by the CI job / ops/push.sh:
#   $APP_DIR/backend   Django project (rsync)
#   $WEB_ROOT          built Vue dist/ (rsync)
#
# Configuration comes from the environment (defaults below match the production domains).
set -euo pipefail

APP_NAME="${APP_NAME:-delivery}"
APP_USER="${APP_USER:-$(id -un)}"
APP_DIR="${APP_DIR:-/opt/${APP_NAME}}"
WEB_ROOT="${WEB_ROOT:-/var/www/${APP_NAME}}"
FRONTEND_DOMAIN="${FRONTEND_DOMAIN:-delivery.hossam-ameen.online}"
API_DOMAIN="${API_DOMAIN:-api.delivery.hossam-ameen.online}"
BACKEND_PORT="${BACKEND_PORT:-8010}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
SSL_EMAIL="${SSL_EMAIL:-hosamameen948@gmail.com}"
ENABLE_SSL="${ENABLE_SSL:-true}"

BACKEND_DIR="${APP_DIR}/backend"
ENV_FILE="${BACKEND_DIR}/.env"
SERVICE="${APP_NAME}-backend"
DB_NAME="${APP_NAME}"
DB_USER="${APP_NAME}"

log() { printf '\n==> %s\n' "$*"; }
rand() { openssl rand -hex "$(( ${1:-40} / 2 ))"; }  # hex: URL/shell safe

[[ -d "${BACKEND_DIR}" ]] || { echo "Missing ${BACKEND_DIR}: upload the code first." >&2; exit 1; }
[[ -d "${WEB_ROOT}" ]] || { echo "Missing ${WEB_ROOT}: upload the frontend build first." >&2; exit 1; }

# ---------------------------------------------------------------- system packages
log "System packages"
need=()
for pkg in nginx postgresql redis-server python3-venv python3-pip certbot python3-certbot-nginx curl; do
  dpkg -s "$pkg" >/dev/null 2>&1 || need+=("$pkg")
done
if ((${#need[@]})); then
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${need[@]}"
fi
sudo systemctl enable --now postgresql redis-server nginx >/dev/null

# ---------------------------------------------------------------- directories
sudo mkdir -p "${APP_DIR}/media" "${APP_DIR}/static"
sudo chown -R "${APP_USER}:" "${APP_DIR}"
sudo chown -R "${APP_USER}:" "${WEB_ROOT}"

# ---------------------------------------------------------------- .env (secrets are generated once, kept across deploys)
log "Backend environment"
if [[ ! -f "${ENV_FILE}" ]]; then
  DB_PASSWORD="$(rand 32)"
  umask 077
  cat >"${ENV_FILE}" <<EOF
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=$(rand 64)
HEALTH_CHECK_PASSWORD=$(rand 32)
DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}
RATELIMIT_CACHE_URL=redis://127.0.0.1:6379/2
EOF
  umask 022
  # Role + database are created only together with a fresh .env (password lives only there).
  sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER ROLE ${DB_USER} PASSWORD '${DB_PASSWORD}';
  END IF;
END \$\$;
SQL
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
    || sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"
fi

# Settings derived from config: always refreshed so a domain/port change takes effect.
set_env() { # key value
  sed -i "/^$1=/d" "${ENV_FILE}"
  printf '%s=%s\n' "$1" "$2" >>"${ENV_FILE}"
}
SCHEME="http"; [[ "${ENABLE_SSL}" == "true" ]] && SCHEME="https"
set_env ALLOWED_HOSTS "${API_DOMAIN}"
set_env CORS_ALLOWED_ORIGINS "${SCHEME}://${FRONTEND_DOMAIN}"
set_env CSRF_TRUSTED_ORIGINS "${SCHEME}://${API_DOMAIN},${SCHEME}://${FRONTEND_DOMAIN}"
set_env FRONTEND_ORIGIN "${SCHEME}://${FRONTEND_DOMAIN}"
set_env STATIC_PATH "${APP_DIR}/static"
set_env MEDIA_PATH "${APP_DIR}/media"
set_env NUM_PROXIES 1
chmod 600 "${ENV_FILE}"

# ---------------------------------------------------------------- python deps, migrate, static
log "Python environment"
cd "${BACKEND_DIR}"
[[ -d venv ]] || python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements/production.txt

log "Migrate + collectstatic"
set -a; . "${ENV_FILE}"; set +a
venv/bin/python manage.py check --deploy --fail-level ERROR
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput

# ---------------------------------------------------------------- systemd
log "systemd service ${SERVICE}"
unit="/etc/systemd/system/${SERVICE}.service"
tmp="$(mktemp)"
cat >"${tmp}" <<EOF
[Unit]
Description=${APP_NAME} backend (gunicorn)
After=network.target postgresql.service redis-server.service

[Service]
User=${APP_USER}
WorkingDirectory=${BACKEND_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${BACKEND_DIR}/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:${BACKEND_PORT} --workers ${GUNICORN_WORKERS} --timeout 60
Restart=always

[Install]
WantedBy=multi-user.target
EOF
if ! cmp -s "${tmp}" "${unit}" 2>/dev/null; then
  sudo install -m 644 "${tmp}" "${unit}"
  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE}" >/dev/null
fi
rm -f "${tmp}"
sudo systemctl restart "${SERVICE}"

# ---------------------------------------------------------------- nginx
# The site files are regenerated on every deploy, so hardening changes take effect. Before a
# certificate exists they are plain HTTP (certbot needs that); afterwards they are the full TLS form.
log "nginx"
sudo tee /etc/nginx/conf.d/00-delivery-hardening.conf >/dev/null <<'EOF'
server_tokens off;
EOF

sudo tee /etc/nginx/snippets/delivery-proxy.conf >/dev/null <<'EOF'
proxy_pass http://127.0.0.1:__PORT__;
# One trusted hop: overwrite (never append) client-supplied forwarding headers (NUM_PROXIES=1).
proxy_set_header Host              $host;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
EOF
sudo sed -i "s/__PORT__/${BACKEND_PORT}/" /etc/nginx/snippets/delivery-proxy.conf

sudo tee /etc/nginx/snippets/delivery-security-headers.conf >/dev/null <<EOF
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "same-origin" always;
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(self), payment=()" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https://${API_DOMAIN}; manifest-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'" always;
EOF

has_cert() { sudo test -d "/etc/letsencrypt/live/$1"; }

# listen/redirect preamble shared by both sites: $1 = domain
tls_head() {
  if has_cert "$1" && [[ "${ENABLE_SSL}" == "true" ]]; then
    cat <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $1;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $1;
    ssl_certificate /etc/letsencrypt/live/$1/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$1/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
EOF
  else
    printf 'server {\n    listen 80;\n    listen [::]:80;\n    server_name %s;\n' "$1"
  fi
}

write_sites() {
  {
    tls_head "${API_DOMAIN}"
    cat <<EOF
    client_max_body_size 10m;

    location /static/ { alias ${APP_DIR}/static/; }
    location /media/  { alias ${APP_DIR}/media/; add_header X-Content-Type-Options "nosniff" always; }

    # Credentials only: small bodies (VULN-014).
    location /api/v1/auth/ {
        client_max_body_size 64k;
        include /etc/nginx/snippets/delivery-proxy.conf;
    }

    location / {
        include /etc/nginx/snippets/delivery-proxy.conf;
    }
}
EOF
  } | sudo tee "/etc/nginx/sites-available/${API_DOMAIN}.conf" >/dev/null

  {
    tls_head "${FRONTEND_DOMAIN}"
    cat <<EOF
    root ${WEB_ROOT};
    index index.html;
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml application/manifest+json;
    include /etc/nginx/snippets/delivery-security-headers.conf;

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        include /etc/nginx/snippets/delivery-security-headers.conf;
    }
    location = /index.html {
        add_header Cache-Control "no-cache";
        include /etc/nginx/snippets/delivery-security-headers.conf;
    }
    location = /sw.js {
        add_header Cache-Control "no-cache";
        include /etc/nginx/snippets/delivery-security-headers.conf;
    }
    location / { try_files \$uri \$uri/ /index.html; }
}
EOF
  } | sudo tee "/etc/nginx/sites-available/${FRONTEND_DOMAIN}.conf" >/dev/null

  for d in "${FRONTEND_DOMAIN}" "${API_DOMAIN}"; do
    sudo ln -sf "/etc/nginx/sites-available/${d}.conf" "/etc/nginx/sites-enabled/${d}.conf"
  done
  sudo nginx -t
  sudo systemctl reload nginx
}

write_sites

# ---------------------------------------------------------------- TLS (skips domains that already have a certificate)
if [[ "${ENABLE_SSL}" == "true" ]]; then
  log "Let's Encrypt"
  issued=0
  for d in "${FRONTEND_DOMAIN}" "${API_DOMAIN}"; do
    if has_cert "$d"; then
      echo "certificate for ${d} already present"
    else
      sudo certbot certonly --nginx --non-interactive --agree-tos -m "${SSL_EMAIL}" -d "${d}"
      issued=1
    fi
  done
  ((issued)) && write_sites
fi

# ---------------------------------------------------------------- health check (fails the deploy)
log "Health check"
ok=0
for _ in $(seq 1 20); do
  code="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Host: ${API_DOMAIN}" -H 'X-Forwarded-Proto: https' \
    -H "X-Health-Check-Token: ${HEALTH_CHECK_PASSWORD}" \
    "http://127.0.0.1:${BACKEND_PORT}/api/v1/health/" || true)"
  [[ "${code}" == "200" ]] && { ok=1; break; }
  sleep 2
done
if ((ok == 0)); then
  echo "Backend unhealthy (last HTTP ${code:-none}). Recent logs:" >&2
  sudo journalctl -u "${SERVICE}" -n 30 --no-pager >&2
  exit 1
fi
echo "Backend healthy."
