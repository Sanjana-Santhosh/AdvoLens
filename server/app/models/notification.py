from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class NotificationType(str, enum.Enum):
    ISSUE_CREATED = "issue_created"
    STATUS_UPDATED = "status_updated"
    ISSUE_RESOLVED = "issue_resolved"
    DUPLICATE_DETECTED = "duplicate_detected"
    ISSUE_ASSIGNED = "issue_assigned"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    type = Column(String, nullable=False)  # Store enum value as string
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # For anonymous tracking - use random token stored in citizen's localStorage
    citizen_token = Column(String, index=True, nullable=True)
    
    # Relationship to issue
    issue = relationship("Issue", back_populates="notifications")
