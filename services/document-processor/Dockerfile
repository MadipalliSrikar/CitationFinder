FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared module first and install it
COPY shared/ /app/shared/
RUN cd /app/shared && pip install -e .

# Now copy and install requirements
COPY services/document-processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm --no-cache-dir

# Copy service code
COPY services/document-processor/src/ /app/src/

# Set Python path to include shared module
ENV PYTHONPATH=/app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]