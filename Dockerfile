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

# Install system dependencies for healthcheck + weasyprint PDF rendering + CJK fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --extra web --extra pdf --no-dev --frozen

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY main.py ./

# Copy frontend build output
COPY --from=frontend-build /build/dist ./web/dist/

# Create data directories
RUN mkdir -p /app/knowledge_base /app/uploads /app/output

# Run as non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with uv
CMD ["uv", "run", "uvicorn", "src.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
