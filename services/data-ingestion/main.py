import time  # Must be at the very top
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel

from shared.models import Paper, Author
from src.core.database import get_db
from src.core.pubmed_service import PubMedService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI Models
class AuthorResponse(BaseModel):
    name: str

    class Config:
        from_attributes = True

class PaperResponse(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str]
    publication_date: Optional[datetime]
    journal: Optional[str]
    authors: List[AuthorResponse]

    class Config:
        from_attributes = True

class IngestRequest(BaseModel):
    query: str
    limit: int = 10

class IngestResponse(BaseModel):
    message: str
    ingested_count: int
    papers: List[PaperResponse]

# FastAPI App
app = FastAPI(title="Data Ingestion Service")
pubmed_service = PubMedService()

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check database connection
        await db.execute("SELECT 1")
        
        # Check PubMed API
        await pubmed_service.search_papers("test", 1)
        
        return {
            "status": "healthy",
            "database": "connected",
            "pubmed_api": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

async def store_paper(db: AsyncSession, paper_data: dict) -> Paper:
    """Store paper and related data in the database"""
    try:
        # Check if paper already exists
        existing_paper = await db.execute(
            select(Paper).where(Paper.pmid == paper_data['pmid'])
        )
        existing_paper = existing_paper.scalar_one_or_none()
        
        if existing_paper:
            return existing_paper
            
        # Create new paper
        paper = Paper(
            pmid=paper_data['pmid'],
            title=paper_data['title'],
            abstract=paper_data['abstract'],
            publication_date=paper_data['publication_date'],
            journal=paper_data['journal'],
            full_text=paper_data.get('full_text', '')
        )
        
        # Add authors
        for author_name in paper_data['authors']:
            # Check if author exists
            existing_author = await db.execute(
                select(Author).where(Author.name == author_name)
            )
            existing_author = existing_author.scalar_one_or_none()
            
            if existing_author:
                author = existing_author
            else:
                author = Author(name=author_name)
                db.add(author)
            
            paper.authors.append(author)
        
        # Add paper to session
        db.add(paper)
        await db.commit()
        await db.refresh(paper)
        
        return paper
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing paper: {str(e)}")
        raise

@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Starting ingestion for query: {request.query}")
        
        # Search for papers
        pmids = await pubmed_service.search_papers(request.query, request.limit)
        
        stored_papers = []
        for pmid in pmids:
            try:
                # Fetch detailed paper data - no sleep needed as PubMedService handles rate limiting
                paper_details = await pubmed_service.fetch_paper_details(pmid)
                
                if paper_details:
                    paper = await store_paper(db, paper_details)
                    paper_response = PaperResponse.from_orm(paper)
                    stored_papers.append(paper_response)
                    
            except Exception as e:
                logger.error(f"Error processing paper {pmid}: {str(e)}")
                continue
        
        return IngestResponse(
            message=f"Successfully ingested papers for query: {request.query}",
            ingested_count=len(stored_papers),
            papers=stored_papers
        )
        
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/papers", response_model=List[PaperResponse])
async def list_papers(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """List all ingested papers with pagination"""
    try:
        # Create a select statement
        query = select(Paper).options(
            selectinload(Paper.authors)
        ).offset(skip).limit(limit)
        
        # Execute the query
        result = await db.execute(query)
        
        # Get all papers
        papers = result.scalars().all()
        
        # Convert to PaperResponse objects
        return [PaperResponse.from_orm(paper) for paper in papers]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/papers/{pmid}", response_model=PaperResponse)
async def get_paper(
    pmid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific paper by PMID"""
    try:
        query = select(Paper).where(Paper.pmid == pmid).options(
            selectinload(Paper.authors)
        )
        result = await db.execute(query)
        paper = result.scalar_one_or_none()
        
        if paper is None:
            raise HTTPException(status_code=404, detail="Paper not found")
            
        return PaperResponse.from_orm(paper)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)