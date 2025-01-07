from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Research Paper RAG Service"
    debug: bool = False
    
    # Model Configuration
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    embedding_dim: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 64
    
    # Database Configuration
    DB_HOST: str = ""
    DB_PORT: str = "25060"
    DB_NAME: str = "defaultdb"
    DB_USER: str = "doadmin"
    DB_PASSWORD: str = ""
    
    # pgvector Configuration
    PGVECTOR_TABLE: str = "paper_embeddings"
    
    

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()