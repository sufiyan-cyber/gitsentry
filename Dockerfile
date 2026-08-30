# =============================================================================
# Multi-stage Dockerfile for GitSentry Webhook Receiver on Cloud Run
# =============================================================================

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PYTHONPATH=/app

# Copy installed wheels to /usr/local
COPY --from=builder /install /usr/local

# Copy application source
COPY common/ /app/common/
COPY services/ /app/services/

# Security: Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD exec uvicorn services.receiver.app:app --host 0.0.0.0 --port ${PORT} --workers 2
