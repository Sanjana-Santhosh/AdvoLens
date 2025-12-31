"""
Engagement models: Votes and Comments for community participation.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class Vote(Base):
    """
    Vote model for upvoting/downvoting issues.
    Uses citizen_token for anonymous tracking (same as notifications).
    """
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    citizen_token = Column(String, index=True, nullable=False)
    vote_type = Column(String, nullable=False)  # "upvote" or "downvote"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    issue = relationship("Issue", back_populates="votes")


class Comment(Base):
    """
    Comment model for community discussion on issues.
    Uses citizen_token for anonymous tracking.
    """
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    citizen_token = Column(String, index=True, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    issue = relationship("Issue", back_populates="comments")
