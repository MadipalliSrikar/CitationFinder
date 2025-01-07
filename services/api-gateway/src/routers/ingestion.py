from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, Any

from ..core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])

@router.post("/", response_model=Dict[str, Any])
async def ingest_data(query: Dict[str, Any]):
    """
    Ingest data from PubMed based on query
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.DATA_INGESTION_URL}/ingest",
                json=query
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, 
                          detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))