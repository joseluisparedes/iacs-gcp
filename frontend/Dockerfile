# ==============================================================================
# BASE STAGE (Node.js 24 LTS)
# ==============================================================================
FROM node:24-alpine AS base

WORKDIR /app

RUN apk add --no-cache curl libc6-compat

# ==============================================================================
# DEVELOPMENT STAGE
# ==============================================================================
FROM base AS development

ENV NODE_ENV=development \
    HOST=0.0.0.0 \
    PORT=3000

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# ==============================================================================
# BUILDER STAGE
# ==============================================================================
FROM base AS builder

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ==============================================================================
# PRODUCTION STAGE (Google Cloud Run Compatible)
# ==============================================================================
FROM node:24-alpine AS production

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=8080

WORKDIR /app

# Usuario no privilegiado
USER node

COPY --chown=node:node --from=builder /app/.output ./.output

EXPOSE 8080

CMD ["node", ".output/server/index.mjs"]
