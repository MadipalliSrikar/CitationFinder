from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RAGRequest(BaseModel):
    query: str
    max_context_chunks: int = 5

class SourceChunk(BaseModel):
    text: str
    document_id: str
    title: str
    score: float

class RAGResponse(BaseModel):
    query: str
    response: str
    sources: List[SourceChunk]
    metadata: dict

class DocumentInput(BaseModel):
    document_id: str
    title: str
    content: str
    metadata: dict = {}

class IndexStats(BaseModel):
    document_count: int
    last_updated: datetime
    embedding_model: str
    index_size: int

class PaperQuery(BaseModel):
    query: str
    max_results: int = 10

class Paper(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str]
    publication_date: Optional[datetime]
    journal: Optional[str]
    authors: List[dict]

class QueryRequest(BaseModel):
    query: str
    query_type: str

class SearchResponse(BaseModel):
    total_results: int
    results: List[Paper]
    metadata: dict