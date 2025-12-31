"""
Notifications API for AdvoLens

This module provides endpoints for citizens to track their issue notifications
using their anonymous tracking token.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.notification import Notification, NotificationType


router = APIRouter(tags=["notifications"])


# Pydantic schemas
class NotificationResponse(BaseModel):
    id: int
    issue_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_type(cls, obj):
        return cls(
            id=obj.id,
            issue_id=obj.issue_id,
            type=obj.type.value if hasattr(obj.type, 'value') else str(obj.type),
            message=obj.message,
            is_read=obj.is_read,
            created_at=obj.created_at
        )


class NotificationCountResponse(BaseModel):
    total: int
    unread: int


@router.get("/my-notifications", response_model=List[NotificationResponse])
def get_citizen_notifications(
    token: str = Query(..., description="Citizen tracking token"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get notifications for a citizen using their tracking token.
    The token is generated when they submit an issue and stored in localStorage.
    """
    if not token or len(token) < 10:
        raise HTTPException(status_code=400, detail="Invalid tracking token")
    
    notifications = db.query(Notification).filter(
        Notification.citizen_token == token
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    return [NotificationResponse.from_orm_with_type(n) for n in notifications]


@router.get("/count", response_model=NotificationCountResponse)
def get_notification_count(
    token: str = Query(..., description="Citizen tracking token"),
    db: Session = Depends(get_db)
):
    """
    Get count of notifications (total and unread) for a citizen.
    Useful for displaying badge counts in the UI.
    """
    if not token or len(token) < 10:
        raise HTTPException(status_code=400, detail="Invalid tracking token")
    
    total = db.query(Notification).filter(
        Notification.citizen_token == token
    ).count()
    
    unread = db.query(Notification).filter(
        Notification.citizen_token == token,
        Notification.is_read == False
    ).count()
    
    return NotificationCountResponse(total=total, unread=unread)


@router.patch("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    token: str = Query(..., description="Citizen tracking token"),
    db: Session = Depends(get_db)
):
    """
    Mark a specific notification as read.
    Requires the citizen token for verification.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.citizen_token == token
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"status": "success", "message": "Notification marked as read"}


@router.patch("/read-all")
def mark_all_as_read(
    token: str = Query(..., description="Citizen tracking token"),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications as read for a citizen.
    """
    if not token or len(token) < 10:
        raise HTTPException(status_code=400, detail="Invalid tracking token")
    
    updated = db.query(Notification).filter(
        Notification.citizen_token == token,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"status": "success", "message": f"Marked {updated} notifications as read"}


# Helper function to create notifications (used by other modules)
def create_notification(
    db: Session,
    issue_id: int,
    notification_type: NotificationType,
    message: str,
    citizen_token: Optional[str] = None
) -> Notification:
    """
    Create a new notification for a citizen.
    
    Args:
        db: Database session
        issue_id: ID of the related issue
        notification_type: Type of notification
        message: Notification message
        citizen_token: Token to identify the citizen
    
    Returns:
        Created Notification object
    """
    notification = Notification(
        issue_id=issue_id,
        type=notification_type,
        message=message,
        citizen_token=citizen_token
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
