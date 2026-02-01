"""
Content API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from utils.auth import get_current_user, TokenData
from agents.content_agent import content_agent
from agents.orchestrator import orchestrator

router = APIRouter()


class ExplainRequest(BaseModel):
    topic: str
    detail_level: str = "detailed"
    include_examples: bool = True


class MindmapRequest(BaseModel):
    subject: str


@router.post("/explain")
async def explain_concept(
    request: ExplainRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Get detailed explanation of a concept."""
    try:
        result = await orchestrator.handle_topic_learning(
            topic=request.topic,
            detail_level=request.detail_level
        )
        
        logger.info(f"Explanation generated for: {request.topic}")
        return result
    
    except Exception as e:
        logger.error(f"Error explaining concept: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/mindmap")
async def create_mindmap(
    request: MindmapRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a mindmap for a subject."""
    try:
        mindmap = await content_agent.create_mindmap(request.subject)
        logger.info(f"Mindmap created for: {request.subject}")
        return mindmap
    
    except Exception as e:
        logger.error(f"Error creating mindmap: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
