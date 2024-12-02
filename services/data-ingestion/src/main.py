# services/data-ingestion/src/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
import xml.etree.ElementTree as ET
import time
from typing import List, Optional, Dict
import psycopg2
from datetime import datetime

class PubMedService:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = os.getenv('PUBMED_API_KEY', '')  # We'll need to add this to k8s secrets
        
    async def search_papers(self, query: str, max_results: int = 10) -> List[str]:
        """Search PubMed and return PMIDs"""
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pmc',
            'term': f"{query} AND open access[filter]",
            'retmax': max_results,
            'usehistory': 'y',
            'api_key': self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params)
            root = ET.fromstring(response.content)
            id_list = root.findall(".//Id")
            return [id_elem.text for id_elem in id_list]

    async def fetch_paper_details(self, pmid: str) -> Dict:
        """Fetch detailed paper information"""
        fetch_url = f"{self.base_url}efetch.fcgi"
        params = {
            'db': 'pmc',
            'id': pmid,
            'retmode': 'xml',
            'api_key': self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(fetch_url, params=params)
            return self._parse_paper_xml(response.content)

    def _parse_paper_xml(self, xml_content: bytes) -> Dict:
        """Parse paper XML and extract relevant information"""
        root = ET.fromstring(xml_content)
        article = root.find(".//article")
        
        if article is None:
            return {}
            
        title_elem = article.find(".//article-title")
        abstract_elem = article.find(".//abstract")
        
        return {
            "title": self._extract_text(title_elem) if title_elem is not None else "No title",
            "abstract": self._extract_text(abstract_elem) if abstract_elem is not None else "No abstract",
            "pmid": root.find(".//article-id[@pub-id-type='pmc']").text if root.find(".//article-id[@pub-id-type='pmc']") is not None else "Unknown"
        }

    def _extract_text(self, element) -> str:
        if element is None:
            return ""
        return ' '.join(element.itertext()).strip()

# FastAPI Models
class IngestRequest(BaseModel):
    query: str
    limit: int = 10

class PaperDetails(BaseModel):
    pmid: str
    title: str
    abstract: str

class IngestResponse(BaseModel):
    message: str
    ingested_count: int
    papers: List[PaperDetails]

# FastAPI App
app = FastAPI(title="Data Ingestion Service")
pubmed_service = PubMedService()

@app.get("/")
async def root():
    return {"message": "Data Ingestion Service is running"}

@app.get("/health")
async def health_check():
    # We'll add real health checks later
    return {
        "status": "healthy",
        "database": "connected",
        "pubmed_api": "connected"
    }

@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(request: IngestRequest):
    try:
        # Search for papers
        pmids = await pubmed_service.search_papers(request.query, request.limit)
        
        papers = []
        for pmid in pmids:
            # Rate limiting
            time.sleep(0.34)  # ~3 requests per second
            paper_details = await pubmed_service.fetch_paper_details(pmid)
            if paper_details:
                papers.append(PaperDetails(
                    pmid=paper_details['pmid'],
                    title=paper_details['title'],
                    abstract=paper_details['abstract']
                ))
        
        return IngestResponse(
            message=f"Successfully ingested papers for query: {request.query}",
            ingested_count=len(papers),
            papers=papers
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)