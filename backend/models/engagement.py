
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from database.types import UUID
import uuid
from datetime import datetime
import enum

from database.connection import Base

class ContentType(str, enum.Enum):
    PLAN = "plan"
    CHAPTER = "chapter"
    QUIZ = "quiz"
    SIMULATION = "simulation"

class EngagementAction(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    RATE = "rate"

class Engagement(Base):
    __tablename__ = "engagements"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content_type = Column(String(50), nullable=False) # Store as string for flexibility, validated by Pydantic
    content_id = Column(String(255), nullable=False)
    
    action = Column(String(20), nullable=False) # like, dislike, rate
    value = Column(Integer, nullable=False) # 1/-1 for like/dislike, 1-5 for rate
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="engagements")
