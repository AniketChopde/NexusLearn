"""
Search API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from utils.auth import get_current_user, TokenData
from agents.search_agent import search_agent

router = APIRouter()


class DeepSearchRequest(BaseModel):
    query: str
    search_depth: str = "comprehensive"


class ResourceSearchRequest(BaseModel):
    topic: str
    resource_type: str = "all"


@router.post("/deep")
async def deep_search(
    request: DeepSearchRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Perform deep search with analysis."""
    try:
        results = await search_agent.deep_search(
            query=request.query,
            search_depth=request.search_depth
        )
        
        logger.info(f"Deep search completed for: {request.query}")
        return results
    
    except Exception as e:
        logger.error(f"Error in deep search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/resources")
async def search_resources(
    request: ResourceSearchRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Search for learning resources."""
    try:
        resources = await search_agent.find_resources(
            topic=request.topic,
            resource_type=request.resource_type
        )
        
        logger.info(f"Resources found for: {request.topic}")
        return {"topic": request.topic, "resources": resources}
    
    except Exception as e:
        logger.error(f"Error searching resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
