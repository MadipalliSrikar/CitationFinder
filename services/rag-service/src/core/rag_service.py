from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
from llama_index.vector_stores.postgres import PGVectorStore
import logging
import ssl
from sqlalchemy.exc import SQLAlchemyError
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .config import Settings as AppSettings
from shared.models import Paper

logger = logging.getLogger(__name__)

# Global configuration using Settings
Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")  # Local embedding model

class RAGServiceError(Exception):
    """Base exception for RAG service errors"""
    pass

class RAGService:
    def __init__(self, settings: AppSettings, db: AsyncSession):
        """Initialize RAG service with database connection"""
        self.settings = self._validate_settings(settings)
        self.db = db
        self.vector_store: Optional[PGVectorStore] = None
        self._init_services()

    def _validate_settings(self, settings: AppSettings) -> AppSettings:
        """Validate settings and ensure required fields are present"""
        required_fields = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'PGVECTOR_TABLE']
        missing_fields = [field for field in required_fields if not getattr(settings, field, None)]
        if missing_fields:
            raise RAGServiceError(f"Missing required settings: {', '.join(missing_fields)}")
        return settings

    def _init_services(self):
        """Initialize vector store and index"""
        try:
            # Create SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
            # URL encode the password
            import urllib.parse
            encoded_password = urllib.parse.quote_plus(self.settings.DB_PASSWORD)
        
            # Create connection strings directly
            sync_connection_url = f"postgresql+psycopg2://{self.settings.DB_USER}:{encoded_password}@{self.settings.DB_HOST}:{self.settings.DB_PORT}/{self.settings.DB_NAME}?sslmode=require"
            async_connection_url = f"postgresql+asyncpg://{self.settings.DB_USER}:{encoded_password}@{self.settings.DB_HOST}:{self.settings.DB_PORT}/{self.settings.DB_NAME}?ssl=require"

            # Set up settings to explicitly disable LLM
            from llama_index.core import Settings
            Settings.llm = None  # Explicitly disable LLM
            
            self.vector_store = PGVectorStore(
                connection_string=sync_connection_url,
                async_connection_string=async_connection_url,
                schema_name="public",
                table_name=self.settings.PGVECTOR_TABLE,
                embed_dim=384
            )

            # Create index with vector store
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store
            )
            

            if not self.vector_store:
                raise ValueError("Failed to create vector store")

            logger.info(f"RAG service initialized successfully with table: {self.settings.PGVECTOR_TABLE}")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}")
            raise

    async def create_index_from_processed_papers(self) -> str:
        """Create search index from processed papers"""
        if not self.vector_store:
            raise RAGServiceError("Vector store not initialized")
            
        try:
            # Get all processed papers from database
            stmt = select(Paper)
            result = await self.db.execute(stmt)
            papers = result.scalars().all()

            if not papers:
                logger.warning("No papers found in database")
                return "No papers available for indexing"

            logger.info(f"Creating index from {len(papers)} papers")
            documents = []
            
            for paper in papers:
                if not paper.title or not paper.pmid:
                    logger.warning(f"Skipping paper with missing required fields: {paper.pmid}")
                    continue
                    
                # Combine paper content
                content = f"""
                Title: {paper.title}
                Abstract: {paper.abstract or ''}
                """
                
                # Create document with metadata
                doc = Document(
                    text=content,
                    metadata={
                        "pmid": paper.pmid,
                        "title": paper.title,
                        "indexed_at": datetime.utcnow().isoformat()
                    }
                )
                documents.append(doc)

            # Create storage context and index (Settings automatically handles embed_model)
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context
            )

            logger.info(f"Successfully created index with {len(documents)} documents")
            return f"Index created successfully with {len(documents)} papers"

        except SQLAlchemyError as e:
            logger.error(f"Database error during indexing: {str(e)}")
            raise RAGServiceError(f"Failed to fetch papers: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise RAGServiceError(f"Index creation failed: {str(e)}")

    async def query_papers(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        try:
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="no_text"
            )
            
            response = query_engine.query(query)
            
            sources = []
            for node in response.source_nodes:
                sources.append({
                    "text": node.text[:500],
                    "pmid": node.metadata.get("pmid"),
                    "title": node.metadata.get("title"),
                    "score": float(node.score) if hasattr(node, 'score') else 0.0
                })

            return {
                "query": query,
                "sources": sources,
                "metadata": {
                    "papers_retrieved": len(sources)
                }
            }

        except Exception as e:
            logger.error(f"Error querying papers: {str(e)}")
            raise