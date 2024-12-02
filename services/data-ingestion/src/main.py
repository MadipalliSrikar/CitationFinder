# services/data-ingestion/src/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
from typing import List, Optional

app = FastAPI(title="Data Ingestion Service")

# Request model
class IngestRequest(BaseModel):
    query: str
    limit: int = 10

# Response models
class IngestResponse(BaseModel):
    message: str
    ingested_count: int
    documents: List[str]

@app.get("/")
async def root():
    return {"message": "Data Ingestion Service is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",  # We'll implement actual DB check later
        "pubmed_api": "connected"  # We'll implement actual API check later
    }

@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(request: IngestRequest):
    try:
        # Here we'll implement your PubMed ingestion code
        # For now, return mock response
        return {
            "message": f"Started ingestion for query: {request.query}",
            "ingested_count": request.limit,
            "documents": [f"doc_{i}" for i in range(request.limit)]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)