from fastapi import FastAPI, HTTPException, Depends
from .models.schemas import (
    PaperQuery, Paper, ProcessingRequest, 
    QueryRequest, ProcessingResponse, 
    SearchResponse, StatusResponse
)
from .core.research_service import ResearchService
from .core.pubmed_service import PubMedService
from .core.config import get_settings
from .utils.logger import setup_logger
from typing import List

logger = setup_logger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name)

# Initialize services
research_service = ResearchService()
pubmed_service = PubMedService()

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Health check endpoint"""
    return StatusResponse(
        status="healthy",
        message="Service is running"
    )

@app.post("/papers/search")
async def search_papers(query: PaperQuery):
    """Search for papers in PubMed Central"""
    try:
        pmids = await pubmed_service.search_papers(
            query.query, 
            query.max_results
        )
        papers = []
        for pmid in pmids:
            try:
                paper_details = await pubmed_service.fetch_paper_details(pmid)
                # Truncate abstract if it's too long
                if len(paper_details['abstract']) > 300:
                    paper_details['abstract'] = paper_details['abstract'][:300] + "..."
                
                # Limit authors to first 5
                if len(paper_details['authors']) > 5:
                    # Keep only the first 5 authors as proper Author objects
                    paper_details['authors'] = paper_details['authors'][:5]
                    # Add author count to the paper title instead
                    paper_details['title'] = f"{paper_details['title']} ({len(paper_details['authors'])} authors)"
                
                papers.append(Paper(**paper_details))
            except Exception as e:
                logger.error(f"Error processing paper {pmid}: {str(e)}")
                continue
                
        return papers
    except Exception as e:
        logger.error(f"Error searching papers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process", response_model=ProcessingResponse)
async def process_text(request: ProcessingRequest):
    """Process text using T5"""
    try:
        result = await research_service.process_with_t5(
            request.text,
            request.task
        )
        return ProcessingResponse(**result)
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def create_index(papers: List[Paper]):
    """Create search index from papers"""
    try:
        result = await research_service.create_index([
            paper.model_dump() for paper in papers
        ])
        return {"message": result}
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_index(request: QueryRequest):
    """Search the indexed papers"""
    try:
        result = await research_service.query_index(
            request.query,
            request.query_type
        )
        return SearchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/rag/index")
async def create_index(papers: List[Paper]):
    """Create RAG index from papers"""
    try:
        # Convert papers to dict format
        papers_dict = [paper.model_dump() for paper in papers]
        result = await research_service.create_index_from_papers(papers_dict)
        return {"message": result}
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query", response_model=SearchResponse)
async def query_papers(request: QueryRequest):
    """Query papers using RAG"""
    try:
        result = await research_service.query_papers(
            request.query,
            request.query_type
        )
        return SearchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error querying papers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))