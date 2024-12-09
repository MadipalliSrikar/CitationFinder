from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import text
import logging
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel

from src.core.database import get_db
from src.core.processor import DocumentProcessor
from shared.models import Paper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Processor Service")
processor = DocumentProcessor()

class ProcessResponse(BaseModel):
    pmid: str
    processed_entities: Dict[str, list]
    text_length: int

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check service health including database connection"""
    try:
        await db.execute(text("SELECT 1"))  # Using text() for raw SQL
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

@app.post("/process/{pmid}", response_model=ProcessResponse)
async def process_document(pmid: str, db: AsyncSession = Depends(get_db)):
    """Process a document and extract entities"""
    try:
        # Get paper from database
        stmt = (
            select(Paper)
            .where(Paper.pmid == pmid)
            .options(selectinload(Paper.authors))
        )
        result = await db.execute(stmt)
        paper = result.scalar_one_or_none()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Prepare paper data for processing
        paper_dict = {
            "pmid": paper.pmid,
            "title": paper.title,
            "abstract": paper.abstract,
            "journal": paper.journal,
            "publication_date": paper.publication_date
        }
        
        # Process the paper
        result = await processor.process_document(paper_dict)
        
        return ProcessResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))