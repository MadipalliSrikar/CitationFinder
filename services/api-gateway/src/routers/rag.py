from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, Any

from ..core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

@router.post("/index", response_model=Dict[str, Any])
async def create_index():
    """
    Create RAG index from processed papers
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.RAG_SERVICE_URL}/rag/index",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=Dict[str, Any])
async def query_papers(query: Dict[str, Any]):
    """
    Query papers using RAG
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.RAG_SERVICE_URL}/rag/query",
                json=query,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))