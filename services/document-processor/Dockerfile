FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install shared package first
COPY shared/ ./shared/
RUN pip install -e ./shared/

# Install requirements
COPY services/document-processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spacy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY services/document-processor/src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]