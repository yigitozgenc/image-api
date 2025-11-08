# Multi-stage Docker build with UV package manager
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install UV
RUN pip install --no-cache-dir uv

# Copy dependency files and source code (needed for package build)
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Copy lockfile if it exists, otherwise generate it
COPY uv.lock* ./

# Generate lockfile if it doesn't exist, then sync dependencies
RUN if [ ! -f uv.lock ]; then uv lock; fi && \
    uv sync --frozen --no-group dev || uv sync --no-group dev

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install UV for runtime package reinstall
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./
COPY uv.lock* ./

# Copy application source
COPY ./src /app/src

# Copy scripts for ingestion
COPY ./scripts /app/scripts

# Reinstall package in editable mode pointing to correct path
RUN uv sync --frozen --no-group dev || uv sync --no-group dev

# Set Python path and activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application with access logs enabled
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "image_api.service:app", "--host", "0.0.0.0", "--port", "8000", "--access-log"]

