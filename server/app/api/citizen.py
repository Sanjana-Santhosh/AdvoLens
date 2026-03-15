"""
Citizen API for AdvoLens

Provides cross-device token claiming and aggregated issue feed.
No DB schema changes — tokens are already the identity key.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.issue import Issue
from app.models.notification import Notification

router = APIRouter(tags=["citizen"])


class MergeTokensRequest(BaseModel):
    tokens: List[str]


@router.get("/token/{token}/summary")
def get_token_summary(token: str, db: Session = Depends(get_db)):
    """
    Preview a citizen token before claiming it on a new device.

    Returns issue count, statuses, and last activity date so the user
    can confirm they are entering the correct token.
    """
    issues = db.query(Issue).filter(Issue.citizen_token == token).all()

    if not issues:
        raise HTTPException(status_code=404, detail="Token not found or has no associated issues")

    statuses = [i.status for i in issues]
    last_activity = max((i.created_at for i in issues), default=None)

    return {
        "token": token,
        "issue_count": len(issues),
        "statuses": statuses,
        "last_activity": last_activity.isoformat() if last_activity else None,
    }


@router.post("/tokens/merge")
def merge_tokens(body: MergeTokensRequest, db: Session = Depends(get_db)):
    """
    Return an aggregated feed for multiple citizen tokens.

    Pure read — no DB merge, no schema change.
    The frontend stores the token list in localStorage; this endpoint
    performs a union query and returns combined issues + notifications.
    """
    if not body.tokens:
        raise HTTPException(status_code=400, detail="At least one token is required")

    if len(body.tokens) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 tokens per request")

    issues = (
        db.query(Issue)
        .filter(Issue.citizen_token.in_(body.tokens))
        .order_by(Issue.created_at.desc())
        .all()
    )

    notifications = (
        db.query(Notification)
        .filter(Notification.citizen_token.in_(body.tokens))
        .order_by(Notification.created_at.desc())
        .all()
    )

    return {
        "tokens": body.tokens,
        "issues": [
            {
                "id": i.id,
                "caption": i.caption,
                "status": i.status,
                "department": (
                    i.department.value if hasattr(i.department, "value") else str(i.department)
                ),
                "image_url": i.image_url,
                "created_at": i.created_at.isoformat(),
                "citizen_token": i.citizen_token,
            }
            for i in issues
        ],
        "notifications": [
            {
                "id": n.id,
                "issue_id": n.issue_id,
                "type": n.type,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "total_issues": len(issues),
        "unread_count": sum(1 for n in notifications if not n.is_read),
    }
