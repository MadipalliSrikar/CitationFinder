# Data ingestion service main FastAPI application
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import contextlib

from src.core.database import get_db, AsyncSessionLocal
from shared.models import Paper, Author
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
    model_config = ConfigDict(from_attributes=True)

class PaperResponse(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str]
    publication_date: Optional[datetime]
    journal: Optional[str]
    authors: List[AuthorResponse]
    model_config = ConfigDict(from_attributes=True)

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

async def store_paper(db: AsyncSession, paper_data: dict) -> Paper:
    try:
        # Check if the paper already exists
        query = select(Paper).options(selectinload(Paper.authors)).where(Paper.pmid == paper_data['pmid'])
        result = await db.execute(query)
        existing_paper = result.scalar_one_or_none()
        
        if existing_paper:
            return existing_paper
        
        # Create a new paper object
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
            query = select(Author).where(Author.name == author_name)
            result = await db.execute(query)
            existing_author = result.scalar_one_or_none()
            
            if existing_author:
                author = existing_author
            else:
                author = Author(name=author_name)
                db.add(author)
            paper.authors.append(author)
        
        # Add and flush the paper to the session
        db.add(paper)
        await db.flush()
        
        # Refresh the paper (relationships will be lazy-loaded or eagerly loaded)
        await db.refresh(paper)
        
        return paper

    except Exception as e:
        logger.error(f"Error storing paper: {str(e)}")
        raise



@contextlib.asynccontextmanager
async def transaction(session):
    if not session.in_transaction():
        async with session.begin():
            yield
    else:
        yield

@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    stored_papers = []
    try:
        logger.info(f"Starting ingestion for query: {request.query}, limit: {request.limit}")
        
        # Initialize PubMed service
        async with PubMedService() as pubmed:  # Use context manager if not already initialized
            logger.info("Searching PubMed for papers...")
            pmids = await pubmed.search_papers(request.query, request.limit)
            logger.info(f"Found {len(pmids)} papers: {pmids}")
            
            for pmid in pmids:
                try:
                    logger.info(f"Fetching details for PMID: {pmid}")
                    paper_details = await pubmed.fetch_paper_details(pmid)
                    
                    if paper_details:
                        logger.info(f"Processing paper: {paper_details.get('title', '')[:50]}...")
                        async with AsyncSessionLocal() as session:
                            async with session.begin():
                                paper = await store_paper(session, paper_details)
                                logger.info(f"Stored paper with PMID: {paper.pmid}")
                                
                                # Explicitly load authors
                                await session.refresh(paper, ['authors'])
                                authors = [AuthorResponse(name=author.name) for author in paper.authors]
                                
                                paper_response = PaperResponse(
                                    pmid=paper.pmid,
                                    title=paper.title,
                                    abstract=paper.abstract,
                                    publication_date=paper.publication_date,
                                    journal=paper.journal,
                                    authors=authors
                                )
                                stored_papers.append(paper_response)
                                logger.info(f"Added paper to response: {paper.pmid}")
                except Exception as e:
                    logger.error(f"Error processing paper {pmid}: {str(e)}")
                    continue
        
        logger.info(f"Completed ingestion. Total papers stored: {len(stored_papers)}")
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