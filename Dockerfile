FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for production
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user early for security
RUN useradd --create-home --shell /bin/bash brainforge

# Copy requirements first for better caching
COPY pyproject.toml .

# Install Python dependencies in two stages
RUN pip install --no-cache-dir -e . \
    && pip cache purge

# Copy source code with proper ownership
COPY --chown=brainforge:brainforge src/ ./src/
COPY --chown=brainforge:brainforge config/ ./config/

# Switch to non-root user
USER brainforge

# Expose port
EXPOSE 8000

# Enhanced health checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Readiness probe (for Kubernetes)
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/readiness || exit 1

# Liveness probe (for Kubernetes)
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/liveness || exit 1

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV LOG_LEVEL=INFO
ENV DEBUG=false

# Default command for production
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log"]