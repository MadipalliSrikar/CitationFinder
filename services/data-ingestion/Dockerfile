# Stage 1: Builder
FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install shared package first
COPY shared/ ./shared/
RUN pip install -e ./shared/

# Copy and create wheels
COPY services/data-ingestion/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements.txt \
    && pip wheel --no-cache-dir --wheel-dir=/app/wheels typing-extensions>=4.0

# Stage 2: Final small image
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -r -s /bin/false appuser

# Copy shared package
COPY shared/ ./shared/
RUN pip install -e ./shared/

# Copy wheels and install packages
COPY --from=builder /app/wheels /app/wheels
COPY services/data-ingestion/requirements.txt .

# Install packages
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels -r requirements.txt \
    && pip install --no-cache-dir --no-index --find-links=/app/wheels typing-extensions>=4.0 \
    && rm -rf /app/wheels \
    && rm -rf /root/.cache/pip \
    && find /usr/local/lib/python3.9/site-packages/ \( -name "*.pyc" -o -name "__pycache__" \) -delete

# Copy application code
COPY services/data-ingestion/main.py .
COPY services/data-ingestion/src/ ./src/
COPY services/data-ingestion/alembic.ini .
COPY services/data-ingestion/alembic/ ./alembic/

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]