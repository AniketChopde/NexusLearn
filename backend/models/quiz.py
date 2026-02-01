"""
Quiz models and schemas.
"""

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database.connection import Base
from database.types import UUID, JSON
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class QuizSession(Base):
    """Quiz session database model."""
    
    __tablename__ = "quiz_sessions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    difficulty = Column(String(50), default="medium")  # easy, medium, hard
    questions = Column(JSON, nullable=False)
    answers = Column(JSON, default={})
    score = Column(Float, nullable=True)
    total_questions = Column(Float, nullable=False)
    correct_answers = Column(Float, default=0)
    status = Column(String(50), default="in_progress")  # in_progress, completed
    time_limit_minutes = Column(Integer, nullable=True)
    time_taken_seconds = Column(Float, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="quiz_sessions")


class ChatSession(Base):
    """Chat session database model."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    messages = Column(JSON, default=[])
    context = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")


class SearchCache(Base):
    """Search cache database model."""
    
    __tablename__ = "search_cache"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    query = Column(String(500), nullable=False)
    results = Column(JSON, nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Schemas
class QuestionSchema(BaseModel):
    """Schema for a quiz question."""
    question_id: str
    question_text: str = Field(..., alias="question")
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str
    marks: int = Field(default=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuizGenerate(BaseModel):
    """Schema for generating a quiz."""
    topic: str = Field(..., description="Topic for the quiz")
    subject: str = Field(..., description="Subject area")
    question_count: int = Field(10, ge=1, le=50, description="Number of questions")
    difficulty: str = Field("medium", description="Difficulty level: easy, medium, hard, mixed")
    exam_type: str | None = Field(None, description="Target exam type (e.g., JEE Main, GATE) for PYQs")

class TestCenterGenerate(BaseModel):
    """Schema for generating a test center exam."""
    exam_name: str = Field(..., description="Name of the exam (e.g., JEE, NEET, GATE)")

class QuizSubmit(BaseModel):
    """Schema for submitting quiz answers."""
    quiz_id: uuid.UUID
    answers: Dict[str, str] = Field(..., description="Map of question_id to answer")
    time_taken_seconds: float = Field(..., ge=0)


class QuizResponse(BaseModel):
    """Schema for quiz response."""
    id: uuid.UUID
    topic: str
    subject: str
    difficulty: str
    questions: List[QuestionSchema]
    status: str
    time_limit_minutes: int | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizResultResponse(BaseModel):
    """Schema for quiz result response."""
    id: uuid.UUID
    topic: str
    subject: str
    score: float
    total_questions: int
    correct_answers: int
    time_taken_seconds: float
    answers: Dict[str, str]
    detailed_results: List[Dict[str, Any]]
    completed_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for a chat message."""
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Schema for chat request."""
    session_id: uuid.UUID | None = None
    message: str = Field(..., min_length=1, max_length=2000)
    context: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Schema for chat response."""
    session_id: uuid.UUID
    message: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
