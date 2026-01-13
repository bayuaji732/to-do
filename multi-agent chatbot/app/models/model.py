from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    metadata: Dict[str, Any]
    chart_config: Optional[Dict[str, Any]] = None
    query_results: List[Dict[str, Any]]
    errors: List[str]
    detected_intent: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    row_count: int