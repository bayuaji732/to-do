"""
FastAPI application for the multi-agent chatbot.
"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import app as routes_app, set_dependencies
from app.database.manager import DatabaseManager
from app.services.orchestrator import MultiAgentOrchestrator
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
db_manager: Optional[DatabaseManager] = None
orchestrator: Optional[MultiAgentOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global db_manager, orchestrator

    logger.info("Starting up application...")

    try:
        # Initialize database
        db_manager = DatabaseManager(
            csv_path=settings.dataset_path,
            db_path=settings.duckdb_path
        )
        db_manager.initialize()

        # Initialize orchestrator
        orchestrator = MultiAgentOrchestrator(db_manager)

        set_dependencies(db_manager, orchestrator)

        logger.info("Application started successfully")

        yield  # Application runs here

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    finally:
        logger.info("Shutting down application...")

        if db_manager:
            db_manager.close()

        logger.info("Application shut down")

# Initialize FastAPI app
app = FastAPI(
    title="S&P 500 Multi-Agent Chatbot API",
    description="GenAI-powered chatbot for querying S&P 500 financial data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_app)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )