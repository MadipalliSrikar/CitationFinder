FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/api-gateway/src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]