"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from database.connection import get_db
from models.user import User, UserCreate, UserLogin, UserResponse, TokenResponse
from utils.auth import hash_password, verify_password, create_token_pair, get_current_user, get_current_refresh_user, TokenData

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
    
    Returns:
        Created user information
    """
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user registered: {new_user.email}")
        return new_user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return JWT tokens.
    
    Args:
        credentials: Login credentials
        db: Database session
    
    Returns:
        Access and refresh tokens
    """
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address."
            )
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Please try again."
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support."
            )
        
        # Create tokens
        tokens = create_token_pair(user.id, user.email)
        
        logger.info(f"User logged in: {user.email}")
        return tokens
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        User profile information
    """
    try:
        result = await db.execute(
            select(User).where(User.id == current_user.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: TokenData = Depends(get_current_refresh_user)
):
    """
    Refresh access token using refresh token.
    
    Args:
        current_user: Current user from refresh token
    
    Returns:
        New access and refresh tokens
    """
    try:
        tokens = create_token_pair(current_user.user_id, current_user.email)
        logger.info(f"Token refreshed for user: {current_user.email}")
        return tokens
    
    except Exception as e:
        logger.error(f"Error in refresh_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


# Password Reset Schemas
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timedelta
import uuid
import re
from utils.email import EmailService
from config import settings

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
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
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email.
    """
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated. Please contact support."
            )

        # Block admin accounts from using the public password reset flow
        if user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin accounts cannot use the public password reset. Please contact your system administrator."
            )
            
        # Generate token
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)
        
        await db.commit()
        
        # Send email
        email_service = EmailService()
        host = settings.frontend_url
        
        await email_service.send_reset_password_email(user.email, token, host)
        
        logger.info(f"Password reset email sent to: {user.email}")
        return {"message": "Password reset link sent to your email."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in forgot_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again later."
        )

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid token.
    """
    try:
        # Find user by token
        result = await db.execute(
            select(User).where(User.reset_token == request.token)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link is invalid. Please request a new one."
            )
            
        # Check expiry
        if user.reset_token_expires < datetime.utcnow():
            # Invalidate the expired token
            user.reset_token = None
            user.reset_token_expires = None
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link has expired (valid for 30 minutes). Please request a new one."
            )
            
        # Update password
        user.password_hash = hash_password(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        
        await db.commit()
        
        logger.info(f"Password reset successful for user: {user.email}")
        return {"message": "Password reset successful. You can now log in with your new password."}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again."
        )
