# FraudShield frontend (Next.js). Build from the fraudshield/ folder.
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/yarn.lock* frontend/package-lock.json* ./
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else npm ci; fi
COPY frontend ./
# BACKEND_URL is baked into the rewrite rules at build time.
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
RUN npx next build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production BACKEND_URL=http://backend:8000
COPY --from=build /app ./
USER node
EXPOSE 3000
CMD ["npx", "next", "start", "-H", "0.0.0.0", "-p", "3000"]
