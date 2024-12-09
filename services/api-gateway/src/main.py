from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.routers import ingestion, processor, rag
from src.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API Gateway for Citation Finder Services"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion.router)
app.include_router(processor.router)
app.include_router(rag.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Citation Finder API Gateway",
        "version": "1.0"
    }