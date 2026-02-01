"""
Chat API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import uuid
from datetime import datetime

from database.connection import get_db
from models.quiz import ChatSession, ChatRequest, ChatResponse, ChatMessage
from utils.auth import get_current_user, TokenData
from services.azure_openai import azure_openai_service
from services.vector_store import vector_store_service
from agents.safety_agent import safety_agent
from agents.orchestrator import orchestrator

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message and get AI response."""
    try:
        request_context = jsonable_encoder(request.context or {})

        # Get or create chat session
        chat_session = None
        if request.session_id:
            result = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == request.session_id,
                    ChatSession.user_id == current_user.user_id
                )
            )
            chat_session = result.scalar_one_or_none()
        
        if not chat_session:
            # Create new session (optionally using the requested ID if provided)
            chat_session = ChatSession(
                id=request.session_id if request.session_id else uuid.uuid4(),
                user_id=current_user.user_id,
                title=request.message[:50],
                messages=[],
                context=request_context
            )
            db.add(chat_session)
            logger.info(f"Created new chat session: {chat_session.id}")
        else:
            # If caller provided context updates, persist them for subsequent turns
            if request_context and isinstance(request_context, dict):
                chat_session.context = jsonable_encoder({**(chat_session.context or {}), **request_context})
        
        # Add user message
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.utcnow().isoformat()
        )
        chat_session.messages = jsonable_encoder(chat_session.messages) + [jsonable_encoder(user_message.dict())]

        # LLM-only Chat: Use context provided in request + session history
        req_ctx = request.context or chat_session.context or {}
        
        # Format context for the LLM
        context_str = jsonable_encoder(req_ctx)
        
        # Prepare messages including history
        chat_history = chat_session.messages if isinstance(chat_session.messages, list) else []
        messages_to_send = [{"role": "system", "content": f"""ROLE: Expert AI Teaching Assistant
CONTEXT: {context_str}

RULES:
- Use the provided context to inform your answer.
- Answer clearly and accurately.
- Avoid making things up if not sure.
- Keep the tone helpful and professional."""}]
        
        # Add limited history (last 5 turns)
        for msg in chat_history[-10:]:
            messages_to_send.append({"role": msg.get("role"), "content": msg.get("content")})
            
        # Add current message (handled by chat_session.messages update above, but we need to pass it to openai)
        # Actually we added it to chat_session.messages already, so it's in the loop above.
        
        ai_response = await azure_openai_service.chat_completion(
            messages=messages_to_send,
            temperature=0.7
        )
        sources = [] # No sources as search is disabled

        
        # Add AI message
        ai_message = ChatMessage(
            role="assistant",
            content=ai_response,
            timestamp=datetime.utcnow().isoformat()
        )
        chat_session.messages = jsonable_encoder(chat_session.messages) + [jsonable_encoder(ai_message.dict())]
        
        await db.commit()
        await db.refresh(chat_session)
        
        logger.info(f"Chat message processed for session: {chat_session.id}")
        
        return {
            "session_id": chat_session.id,
            "message": ai_response,
            "sources": sources,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a session."""
    try:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.user_id
            )
        )
        chat_session = result.scalar_one_or_none()
        
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return {
            "session_id": chat_session.id,
            "title": chat_session.title,
            "messages": chat_session.messages,
            "created_at": chat_session.created_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat history"
        )


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session."""
    try:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.user_id
            )
        )
        chat_session = result.scalar_one_or_none()
        
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        await db.delete(chat_session)
        await db.commit()
        
        logger.info(f"Chat session deleted: {session_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )
