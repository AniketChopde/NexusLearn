
from typing import List, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from api.deps import get_current_active_superuser, get_db
from models.user import User, UserResponse

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve users. Only for superusers.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.delete("/users/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a user. Only for superusers.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot delete themselves",
        )
        
    await db.delete(user)
    await db.commit()
    return user
