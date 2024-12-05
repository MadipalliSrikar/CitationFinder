from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel

from src.core.database import get_db
from src.core.processor import DocumentProcessor
from shared.models import Paper, Author

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
    processed_entities: Dict[str, List[str]]
    citation_count: int
    text_length: int

class NetworkResponse(BaseModel):
    total_nodes: int
    total_edges: int
    top_cited: List[tuple]
    network_density: float = 0.0
    average_citations: float = 0.0

class CitationResponse(BaseModel):
    pmid: str
    outgoing_citations: List[str]
    cited_by: List[str]
    citation_count: int
    cited_by_count: int
    citation_depth: int = 0

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check service health including database connection"""
    try:
        await db.execute("SELECT 1")
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
    """Process a document and update citation graph"""
    try:
        # Get paper with related data
        stmt = (
            select(Paper)
            .where(Paper.pmid == pmid)
            .options(
                selectinload(Paper.authors),
                selectinload(Paper.citations),
                selectinload(Paper.cited_by)
            )
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
            "citations": [cite.pmid for cite in (paper.citations or [])],
            "cited_by": [cite.pmid for cite in (paper.cited_by or [])]
        }
        
        # Process the main paper
        result = await processor.process_document(paper_dict)
        
        # Optionally process cited papers
        if paper.citations:
            for cited_paper in paper.citations:
                try:
                    cited_dict = {
                        "pmid": cited_paper.pmid,
                        "title": cited_paper.title,
                        "abstract": cited_paper.abstract,
                        "citations": [cite.pmid for cite in (cited_paper.citations or [])]
                    }
                    await processor.process_document(cited_dict)
                except Exception as e:
                    logger.warning(f"Error processing cited paper {cited_paper.pmid}: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network", response_model=NetworkResponse)
async def get_network():
    """Get citation network statistics"""
    try:
        return processor.get_citation_network()
    except Exception as e:
        logger.error(f"Error getting network: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/citations/{pmid}", response_model=CitationResponse)
async def get_citations(pmid: str, db: AsyncSession = Depends(get_db)):
    """Get citation analysis for a specific paper"""
    try:
        # First ensure paper exists and process it if needed
        stmt = select(Paper).where(Paper.pmid == pmid).options(
            selectinload(Paper.citations),
            selectinload(Paper.cited_by)
        )
        result = await db.execute(stmt)
        paper = result.scalar_one_or_none()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
            
        # Analyze citations
        return await processor.analyze_citations(pmid)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing citations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)