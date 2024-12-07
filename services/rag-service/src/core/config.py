from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Research Paper RAG Service"
    t5_model_name: str = "t5-base"
    max_input_length: int = 512
    max_summary_length: int = 150
    min_summary_length: int = 40
    chunk_size: int = 512
    chunk_overlap: int = 64
    pubmed_api_key: str = ""
    index_path: str = "medical_literature_index"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()