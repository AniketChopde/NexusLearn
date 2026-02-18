"""
Study plan models and schemas.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from database.connection import Base
from database.types import UUID, JSON
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class StudyPlan(Base):
    """Study plan database model."""
    
    __tablename__ = "study_plans"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_type = Column(String(100), nullable=False)
    target_date = Column(Date, nullable=False)
    daily_hours = Column(Integer, nullable=False)
    status = Column(String(50), default="active")  # active, completed, paused
    current_knowledge = Column(JSON, default={})
    recommended_courses = Column(JSON, default=[])  # List of recommended courses
    plan_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="study_plans")
    chapters = relationship("StudyPlanChapter", back_populates="study_plan", cascade="all, delete-orphan")


class StudyPlanChapter(Base):
    """Study plan chapter database model."""
    
    __tablename__ = "study_plan_chapters"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False)
    chapter_name = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    topics = Column(JSON, default=[])
    estimated_hours = Column(Integer, nullable=False)
    order_index = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    resources = Column(JSON, default=[])
    content = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="chapters")


class TopicMindmap(Base):
    """Cached topic mindmap per user & topic_id (moduleId)."""

    __tablename__ = "topic_mindmaps"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(255), nullable=False, index=True)
    kb_hash = Column(String(64), nullable=False, index=True)
    mindmap_json = Column(JSON, default={})
    mindmap_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProgress(Base):
    """User progress tracking model."""
    
    __tablename__ = "user_progress"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    completion_percentage = Column(Float, default=0.0)
    quiz_scores = Column(JSON, default=[])
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_progress")


# Pydantic Schemas
class ChapterCreate(BaseModel):
    """Schema for creating a chapter."""
    chapter_name: str
    subject: str
    topics: List[str]
    estimated_hours: int
    order_index: int


class ChapterResponse(BaseModel):
    """Schema for chapter response."""
    id: uuid.UUID
    chapter_name: str
    subject: str
    topics: List[str]
    estimated_hours: int
    order_index: int
    status: str
    resources: List[Dict[str, Any]]
    content: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class StudyPlanCreate(BaseModel):
    """Schema for creating a study plan. Works for any learning goal: exams, skills (e.g. ML, LangChain), or subjects."""
    exam_type: str = Field(..., description="Learning goal or topic (e.g. Machine Learning, LangChain, UPSC, GATE CS)")
    target_date: date = Field(..., description="Target completion date")
    daily_hours: int = Field(..., ge=1, le=24, description="Daily study hours")
    current_knowledge: Dict[str, Any] = Field(default_factory=dict)
    fast_learn: bool = Field(default=False, description="Whether to prioritize core/foundational topics first")


class StudyPlanResponse(BaseModel):
    """Schema for study plan response."""
    id: uuid.UUID
    exam_type: str
    target_date: date
    daily_hours: int
    status: str
    current_knowledge: Dict[str, Any]
    recommended_courses: List[Dict[str, Any]] = []
    chapters: List[ChapterResponse]
    plan_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudyPlanCreateResponse(BaseModel):
    """Schema for study plan creation response with metadata."""
    study_plan: StudyPlanResponse
    ai_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProgressUpdate(BaseModel):
    """Schema for updating progress."""
    topic: str
    subject: str
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    time_spent_minutes: int = Field(..., ge=0)


class ProgressResponse(BaseModel):
    """Schema for progress response."""
    id: uuid.UUID
    topic: str
    subject: str
    completion_percentage: float
    quiz_scores: List[Dict[str, Any]]
    time_spent_minutes: int
    last_accessed: datetime
    
    class Config:
        from_attributes = True
