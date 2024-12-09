# Description: Dockerfile for the RAG service
FROM python:3.9-slim

WORKDIR /app

# Install only required system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only version of PyTorch to reduce size
RUN pip install --no-cache-dir torch==2.1.1+cpu torchvision==0.16.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Copy and install requirements
COPY services/rag-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared package
COPY shared /app/shared
RUN pip install -e /app/shared

# Copy the rest of the application
COPY services/rag-service/src /app/src

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]