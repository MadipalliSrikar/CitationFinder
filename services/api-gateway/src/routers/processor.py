from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, Any

from ..core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/process", tags=["processor"])

@router.post("/{pmid}", response_model=Dict[str, Any])
async def process_document(pmid: str):
    """
    Process a specific document by PMID
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DOCUMENT_PROCESSOR_URL}/process/{pmid}",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))