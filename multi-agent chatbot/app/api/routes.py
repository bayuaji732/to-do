import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from app.database.manager import DatabaseManager
from app.services.orchestrator import MultiAgentOrchestrator
from app.models.model import QueryRequest, QueryResponse, HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = APIRouter()

_db_manager: Optional[DatabaseManager] = None
_orchestrator: Optional[MultiAgentOrchestrator] = None

def set_dependencies(db: DatabaseManager, orch: MultiAgentOrchestrator):
    """Set global dependencies from main.py"""
    global _db_manager, _orchestrator
    _db_manager = db
    _orchestrator = orch


def get_db_manager() -> DatabaseManager:
    if _db_manager is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return _db_manager


def get_orchestrator() -> MultiAgentOrchestrator:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator

@app.get("/", response_model=HealthResponse)
async def health_check(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Health check endpoint."""
    try:
        # Test database connection
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM sp500_companies")
        row_count = result.iloc[0]['count']
        
        return HealthResponse(
            status="healthy",
            database_connected=True,
            row_count=row_count
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator)):
    """
    Process a user query through the multi-agent system.
    
    Args:
        request: Query request with user question
        
    Returns:
        QueryResponse with answer and metadata
    """    
    try:
        logger.info(f"Received query: {request.query}")
        
        # Process query
        result = orchestrator.process_query(request.query)
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_conversation(orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator)):
    """Reset conversation history."""
    orchestrator.reset_conversation()
    return {"status": "success", "message": "Conversation reset"}


@app.get("/schema")
async def get_schema(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get database schema information."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    schema = db_manager.metadata_manager.get_schema_description()
    columns = db_manager.metadata_manager.get_all_columns()
    
    return {
        "schema": schema,
        "columns": columns,
        "table_name": "sp500_companies"
    }


@app.get("/sample-data")
async def get_sample_data(limit: int = 5, db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get sample data from the dataset."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        sample_df = db_manager.get_sample_data(limit)
        return {
            "data": sample_df.to_dict('records'),
            "columns": sample_df.columns.tolist(),
            "row_count": len(sample_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))