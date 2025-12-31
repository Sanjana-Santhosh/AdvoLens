"""
Engagement API endpoints: Voting and Comments for community participation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.engagement import Vote, Comment
from app.models.issue import Issue


router = APIRouter()


# ========== SCHEMAS ==========

class VoteRequest(BaseModel):
    citizen_token: str
    vote_type: str  # "upvote" or "downvote"


class CommentRequest(BaseModel):
    citizen_token: str
    text: str


class CommentResponse(BaseModel):
    id: int
    issue_id: int
    text: str
    created_at: datetime
    # Don't expose citizen_token for privacy
    
    class Config:
        from_attributes = True


# ========== VOTING ENDPOINTS ==========

@router.post("/{issue_id}/vote")
def vote_issue(issue_id: int, vote_req: VoteRequest, db: Session = Depends(get_db)):
    """
    Vote on an issue. Citizens can upvote or downvote.
    Each citizen can only have one vote per issue.
    """
    # Validate vote type
    if vote_req.vote_type not in ["upvote", "downvote"]:
        raise HTTPException(status_code=400, detail="vote_type must be 'upvote' or 'downvote'")
    
    # Check if issue exists
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Check if already voted
    existing_vote = db.query(Vote).filter(
        Vote.issue_id == issue_id,
        Vote.citizen_token == vote_req.citizen_token
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.vote_type = vote_req.vote_type
    else:
        # Create new vote
        vote = Vote(
            issue_id=issue_id,
            citizen_token=vote_req.citizen_token,
            vote_type=vote_req.vote_type
        )
        db.add(vote)
    
    # Recalculate upvote count
    upvotes = db.query(Vote).filter(
        Vote.issue_id == issue_id,
        Vote.vote_type == "upvote"
    ).count()
    
    issue.upvote_count = upvotes
    issue.priority_score = calculate_priority(issue, upvotes)
    
    db.commit()
    
    return {
        "status": "success",
        "upvotes": upvotes,
        "priority_score": issue.priority_score,
        "your_vote": vote_req.vote_type
    }


@router.delete("/{issue_id}/vote")
def remove_vote(
    issue_id: int, 
    citizen_token: str = Query(..., description="Citizen tracking token"),
    db: Session = Depends(get_db)
):
    """Remove a citizen's vote from an issue."""
    vote = db.query(Vote).filter(
        Vote.issue_id == issue_id,
        Vote.citizen_token == citizen_token
    ).first()
    
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    
    db.delete(vote)
    
    # Recalculate counts
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue:
        upvotes = db.query(Vote).filter(
            Vote.issue_id == issue_id,
            Vote.vote_type == "upvote"
        ).count()
        issue.upvote_count = upvotes
        issue.priority_score = calculate_priority(issue, upvotes)
    
    db.commit()
    
    return {"status": "removed", "upvotes": issue.upvote_count if issue else 0}


@router.get("/{issue_id}/vote")
def get_vote_status(
    issue_id: int,
    citizen_token: str = Query(None, description="Citizen tracking token"),
    db: Session = Depends(get_db)
):
    """Get vote count and current user's vote status."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    user_vote = None
    if citizen_token:
        vote = db.query(Vote).filter(
            Vote.issue_id == issue_id,
            Vote.citizen_token == citizen_token
        ).first()
        if vote:
            user_vote = vote.vote_type
    
    return {
        "upvotes": issue.upvote_count,
        "priority_score": issue.priority_score,
        "your_vote": user_vote
    }


# ========== COMMENTS ENDPOINTS ==========

@router.post("/{issue_id}/comments", response_model=CommentResponse)
def add_comment(issue_id: int, comment_req: CommentRequest, db: Session = Depends(get_db)):
    """Add a comment to an issue."""
    # Check if issue exists
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Validate comment text
    if not comment_req.text.strip():
        raise HTTPException(status_code=400, detail="Comment text cannot be empty")
    
    if len(comment_req.text) > 1000:
        raise HTTPException(status_code=400, detail="Comment too long (max 1000 characters)")
    
    comment = Comment(
        issue_id=issue_id,
        citizen_token=comment_req.citizen_token,
        text=comment_req.text.strip()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


@router.get("/{issue_id}/comments")
def get_comments(
    issue_id: int, 
    skip: int = 0, 
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all comments for an issue, newest first."""
    # Check if issue exists
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    comments = db.query(Comment).filter(
        Comment.issue_id == issue_id
    ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    # Return without citizen_token for privacy
    return [
        {
            "id": c.id,
            "issue_id": c.issue_id,
            "text": c.text,
            "created_at": c.created_at
        }
        for c in comments
    ]


@router.delete("/{issue_id}/comments/{comment_id}")
def delete_comment(
    issue_id: int,
    comment_id: int,
    citizen_token: str = Query(..., description="Citizen tracking token"),
    db: Session = Depends(get_db)
):
    """Delete a comment (only by the author)."""
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.issue_id == issue_id,
        Comment.citizen_token == citizen_token
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    
    db.delete(comment)
    db.commit()
    
    return {"status": "deleted"}


# ========== PRIORITY CALCULATION ==========

def calculate_priority(issue: Issue, upvotes: int) -> int:
    """
    Priority Score Algorithm:
    - Base: upvote count × 10
    - Bonus: +50 if status is Open
    - Age penalty: -1 per day old (max 30 days penalty)
    
    Higher score = higher priority
    """
    score = upvotes * 10
    
    # Status bonus
    if issue.status == "Open":
        score += 50
    elif issue.status == "In Progress":
        score += 25
    
    # Age penalty (older issues gradually lose priority, capped at 30 days)
    if issue.created_at:
        # Handle timezone-aware datetime
        created = issue.created_at
        if created.tzinfo:
            from datetime import timezone
            age_days = (datetime.now(timezone.utc) - created).days
        else:
            age_days = (datetime.utcnow() - created).days
        
        age_penalty = min(age_days, 30)  # Cap at 30 days
        score -= age_penalty
    
    return max(score, 0)  # Never negative
