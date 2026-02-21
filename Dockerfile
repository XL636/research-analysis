# Stage 1: Frontend build
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

# Install system dependencies and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --extra web --no-dev --frozen

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY main.py ./

# Copy frontend build output
COPY --from=frontend-build /build/dist ./web/dist/

# Create data directories
RUN mkdir -p /app/knowledge_base /app/uploads /app/output

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with uv
CMD ["uv", "run", "uvicorn", "src.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
