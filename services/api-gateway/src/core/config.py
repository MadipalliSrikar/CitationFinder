from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Citation Finder API Gateway"
    debug: bool = False
    
    # Service URLs
    DATA_INGESTION_URL: str = "http://localhost:8001"
    DOCUMENT_PROCESSOR_URL: str = "http://localhost:8002"
    RAG_SERVICE_URL: str = "http://localhost:8003"
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()