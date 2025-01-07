FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch
RUN pip install --no-cache-dir torch==2.1.1 torchvision==0.16.1 --extra-index-url https://download.pytorch.org/whl/cpu

# Copy shared module first and install it
COPY shared/ /app/shared/
RUN cd /app/shared && pip install -e .

# Now copy and install requirements
COPY services/rag-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/rag-service/src/ /app/src/

# Set Python path to include shared module
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]