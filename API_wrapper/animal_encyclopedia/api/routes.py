"""
API Routes for Animal Encyclopedia
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import logging

from animal_encyclopedia.api.dependencies import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["encyclopedia"])


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="User query about animals", min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    skip_cache: bool = Field(False, description="Skip cache lookup")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    session_id: str
    query: dict
    routing: dict
    cache: dict
    response: dict
    metadata: dict


class SessionHistoryResponse(BaseModel):
    """Response model for session history."""
    session_id: str
    history: List[dict]
    message_count: int


class StatsResponse(BaseModel):
    """Response model for statistics."""
    router: dict
    cache: dict
    active_sessions: int


@router.post("/query", response_model=QueryResponse)
async def query_animal(
    request: QueryRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    Query the animal encyclopedia.

    This endpoint:
    1. Routes the query to check if it's animal-related
    2. Resolves pronouns using conversation history
    3. Checks semantic cache for similar queries
    4. Generates response using LLM if needed
    5. Caches the response for future similar queries

    **Example queries:**
    - "What family does the red fox belong to?"
    - "How many hearts does an octopus have?"
    - "Why do elephants have large ears?"
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Process query
        result = await orchestrator.process_query(
            session_id=session_id,
            query=request.query,
            skip_cache=request.skip_cache
        )

        return result

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    orchestrator = Depends(get_orchestrator)
):
    """
    Get conversation history for a session.

    Returns all messages exchanged in the session, useful for:
    - Displaying conversation context
    - Debugging anaphora resolution
    - Analyzing user interactions
    """
    try:
        history = orchestrator.get_session_history(session_id)

        return {
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        }

    except Exception as e:
        logger.error(f"Error retrieving session history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    orchestrator = Depends(get_orchestrator)
):
    """
    Clear conversation history for a session.

    Use this to:
    - Start a fresh conversation
    - Reset context when switching topics
    - Clean up old sessions
    """
    try:
        orchestrator.clear_session(session_id)

        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error clearing session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(orchestrator = Depends(get_orchestrator)):
    """
    Get system statistics.

    Returns:
    - Router statistics (thresholds, anchor counts)
    - Cache statistics (hit rate, size)
    - Active session count

    Useful for monitoring and optimization.
    """
    try:
        stats = orchestrator.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/cache/clear")
async def clear_cache(orchestrator = Depends(get_orchestrator)):
    """
    Clear semantic cache (admin endpoint).

    Use with caution - this will:
    - Remove all cached responses
    - Reset cache statistics
    - Require fresh LLM calls for all subsequent queries
    """
    try:
        orchestrator.semantic_cache.clear()

        return {
            "message": "Cache cleared successfully",
            "note": "All future queries will require fresh LLM calls"
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
