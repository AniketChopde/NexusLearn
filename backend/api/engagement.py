
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime

from database.connection import get_db
from models.engagement import Engagement, ContentType, EngagementAction
from api.deps import get_current_user
from models.user import User, UserBase

router = APIRouter()

class EngagementCreate(BaseModel):
    content_type: ContentType
    content_id: str
    action: EngagementAction
    value: int
    comment: Optional[str] = None

class EngagementResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user: Optional[UserBase] = None # Include user details
    content_type: str
    content_id: str
    action: str
    value: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=EngagementResponse)
async def create_engagement(
    data: EngagementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an engagement (like, dislike, rate, etc.).
    If an engagement already exists for this user/content/action, update it.
    """
    # Check for existing engagement
    result = await db.execute(
        select(Engagement).where(
            Engagement.user_id == current_user.id,
            Engagement.content_type == data.content_type.value,
            Engagement.content_id == data.content_id,
            Engagement.action == data.action.value
            # Note: We might want to allow multiple actions (like + rate), 
            # so we filter by action too.
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.value = data.value
        existing.comment = data.comment
        await db.commit()
        await db.refresh(existing)
        existing.user = current_user # Avoid MissingGreenlet on response serialization
        return existing
    
    # Create new
    new_engagement = Engagement(
        user_id=current_user.id,
        content_type=data.content_type.value,
        content_id=data.content_id,
        action=data.action.value,
        value=data.value,
        comment=data.comment
    )
    db.add(new_engagement)
    await db.commit()
    await db.refresh(new_engagement)
    new_engagement.user = current_user # Avoid MissingGreenlet on response serialization
    return new_engagement

@router.get("/me", response_model=Optional[EngagementResponse])
async def get_my_engagement(
    content_type: ContentType,
    content_id: str,
    action: EngagementAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's engagement for specific content.
    """
    result = await db.execute(
        select(Engagement).where(
            Engagement.user_id == current_user.id,
            Engagement.content_type == content_type.value,
            Engagement.content_id == content_id,
            Engagement.action == action.value
        )
    )
    engagement = result.scalar_one_or_none()
    if engagement:
        engagement.user = current_user
    return engagement

@router.get("/all", response_model=list[EngagementResponse])
async def get_all_engagements(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all engagements (Admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await db.execute(
        select(Engagement)
        .options(joinedload(Engagement.user))
        .order_by(Engagement.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    engagements = result.scalars().all()
    return engagements
