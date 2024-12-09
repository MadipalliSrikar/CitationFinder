from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy import text
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime

from src.core.database import get_db
from src.core.rag_service import RAGService
from src.core.config import get_settings

logger = logging.getLogger(__name__)
app = FastAPI(title="RAG Service")
settings = get_settings()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check service health including database connection"""
    try:
        # Using text() for raw SQL
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@app.post("/rag/index")
async def create_index(db: AsyncSession = Depends(get_db)):
    """Create RAG index from processed papers"""
    try:
        rag_service = RAGService(settings, db)
        result = await rag_service.create_index_from_processed_papers()
        return {"message": result}
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query")
async def query_papers(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Query papers using RAG"""
    try:
        rag_service = RAGService(settings, db)
        result = await rag_service.query_papers(
            query=request.query,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        logger.error(f"Error querying papers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))