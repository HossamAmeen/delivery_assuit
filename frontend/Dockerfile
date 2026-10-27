# Local development image: Vite dev server with HMR. No secrets are baked in.
# Build context is ./frontend. Production serving is out of scope for Sprint 01.
FROM node:22-slim

ENV NODE_ENV=development

# Everything below runs as the non-root `node` user, so node_modules (and the named volume
# compose mounts over it) is owned by `node` and Vite can write its dependency cache there.
RUN mkdir -p /app && chown node:node /app
WORKDIR /app
USER node

# Dependencies first so this layer is cached until the lockfile changes.
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node . .

EXPOSE 5173

# VITE_API_URL is the URL the BROWSER uses (host-published backend port), provided by compose.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
