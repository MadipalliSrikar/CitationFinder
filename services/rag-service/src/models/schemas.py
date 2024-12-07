from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Author(BaseModel):
    name: str

class Paper(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    authors: Optional[List[Author]] = Field(default_factory=list)  # Make authors optional with default empty list

class PaperQuery(BaseModel):
    query: str
    max_results: int = 10

class ProcessingRequest(BaseModel):
    text: str
    task: str = "summarize"  # summarize, analyze, extract_methods, find_conclusions

class QueryRequest(BaseModel):
    query: str
    query_type: str = "basic"  # basic, methodology, findings, comparison, limitations

class ProcessingResponse(BaseModel):
    result: str
    processing_time: float

class SearchResponse(BaseModel):
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    processing_time: float

class StatusResponse(BaseModel):
    status: str
    message: str