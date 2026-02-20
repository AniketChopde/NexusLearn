
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from database.connection import get_db
from utils.auth import get_current_user as get_current_user_token
from utils.auth import TokenData

async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the database.
    """
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Check if the current user is a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user
