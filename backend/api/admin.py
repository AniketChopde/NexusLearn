
from typing import List, Any
import uuid
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, EmailStr, field_validator

from api.deps import get_current_active_superuser, get_db
from models.user import User, UserResponse
from utils.auth import hash_password
from utils.email import EmailService
from config import settings
from loguru import logger

router = APIRouter()

# ─── User Management ─────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve users. Only for superusers."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.delete("/users/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete a user. Only for superusers."""
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


# ─── Admin Password Reset (no auth required — public flow for admins) ─────────

class AdminForgotPasswordRequest(BaseModel):
    email: EmailStr


class AdminResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def admin_forgot_password(
    request: AdminForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only password reset flow.
    Only sends a reset email if the email belongs to a superuser account.
    """
    try:
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address.",
            )

        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This email does not belong to an admin account.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This admin account has been deactivated.",
            )

        # Generate token
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)
        await db.commit()

        # Send email with admin reset URL
        email_service = EmailService()
        host = settings.frontend_url
        # Use admin-specific reset URL
        admin_reset_url = f"{host}/admin/reset-password?token={token}"
        await email_service.send_reset_password_email(user.email, token, host, reset_url=admin_reset_url)

        logger.info(f"Admin password reset email sent to: {user.email}")
        return {"message": "Admin password reset link sent to your email."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin_forgot_password: {str(e)}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again later.",
        )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def admin_reset_password(
    request: AdminResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset admin password using a valid token."""
    try:
        result = await db.execute(
            select(User).where(User.reset_token == request.token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link is invalid. Please request a new one.",
            )

        # Ensure it's still a superuser
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This token is not valid for an admin account.",
            )

        if user.reset_token_expires < datetime.utcnow():
            user.reset_token = None
            user.reset_token_expires = None
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link has expired (valid for 30 minutes). Please request a new one.",
            )

        user.password_hash = hash_password(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        await db.commit()

        logger.info(f"Admin password reset successful for: {user.email}")
        return {"message": "Admin password reset successful. You can now log in."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin_reset_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again.",
        )

