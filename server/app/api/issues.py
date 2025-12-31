from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os
import secrets

from app.core.database import get_db
from app.schemas.issue import IssueResponse, IssueCreateResponse
from app.crud import issue as crud_issue
from app.ml.clip_service import clip_service
from app.ml.faiss_manager import faiss_manager
from app.ml.gemini_service import gemini_service
from app.services.notification import notify_issue_resolved, notify_issue_reopened
from app.services.routing_service import assign_department
from app.services.cloudinary_service import upload_image
from app.services.email_service import notify_new_issue
from app.services.geo_service import find_nearby_issues
from app.models.notification import Notification, NotificationType


router = APIRouter(tags=["issues"])

# Use /tmp for temporary files (works on Render)
TEMP_DIR = "/tmp"


class StatusUpdate(BaseModel):
    """Schema for updating issue status"""
    status: str


@router.post("/", response_model=IssueCreateResponse)
async def create_issue(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    lat: float = Form(...),
    lon: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Generate tracking token for anonymous citizen
    tracking_token = secrets.token_urlsafe(16)
    
    # 2. Save temp file (use /tmp for Render compatibility)
    temp_path = f"{TEMP_DIR}/{image.filename}"
    with open(temp_path, "wb+") as file_object:
        shutil.copyfileobj(image.file, file_object)

    # 3. Upload to Cloudinary
    cloud_url = upload_image(temp_path)
    if not cloud_url:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail="Image upload failed")

    # 4. AI Analysis (CLIP for embeddings, Gemini for captioning)
    embedding = clip_service.get_embedding(temp_path)
    gemini_result = gemini_service.analyze_image(temp_path)

    # 5. Clean up temp file
    os.remove(temp_path)

    # 6. Check for Visual Duplicates (CLIP + Faiss)
    visual_duplicate_id = None
    if embedding is not None:
        similar_issues = faiss_manager.search_similar(embedding, threshold=0.92)
        if similar_issues:
            visual_duplicate_id, score = similar_issues[0]
            print(f"👁️ Visual duplicate candidate: Issue #{visual_duplicate_id} with score {score:.3f}")

    # 7. Check for Spatial Duplicates (within 50m)
    spatial_duplicates = find_nearby_issues(db, lat, lon, radius_meters=50)
    spatial_duplicate_ids = [issue.id for issue in spatial_duplicates]
    
    # 8. Combined duplicate logic - if BOTH visual AND spatial match, it's a definite duplicate
    duplicate_of = None
    is_definite_duplicate = False
    
    if visual_duplicate_id and visual_duplicate_id in spatial_duplicate_ids:
        # Both visual AND spatial match = definite duplicate
        duplicate_of = visual_duplicate_id
        is_definite_duplicate = True
        print(f"⚠️ DEFINITE DUPLICATE: Issue #{visual_duplicate_id} matches both visually and spatially!")
    elif visual_duplicate_id:
        # Visual match only - still flag it
        duplicate_of = visual_duplicate_id
        print(f"⚠️ Visual duplicate only: Issue #{visual_duplicate_id}")
    elif spatial_duplicate_ids:
        # Spatial match only - note it but don't flag as duplicate
        print(f"📍 Nearby issues found within 50m: {spatial_duplicate_ids}")

    # 9. AUTO-ASSIGN DEPARTMENT based on AI tags
    assigned_dept = assign_department(gemini_result.get('tags', []))
    print(f"🏛️ Auto-assigned to department: {assigned_dept.value}")

    # 10. Save to DB with Cloudinary URL and tracking token
    new_issue = crud_issue.create_issue(
        db=db,
        title=title or gemini_result.get('caption'),
        description=description,
        image_url=cloud_url,
        caption=gemini_result.get('caption'),
        tags=gemini_result.get('tags'),
        lat=lat,
        lon=lon,
        department=assigned_dept,
        citizen_token=tracking_token,
    )

    # 11. Add to Faiss Index for future searches
    if embedding is not None:
        faiss_manager.add_vector(embedding, new_issue.id)

    # 12. Create notification for citizen
    dept_label = assigned_dept.value.replace('_', ' ').title()
    notification = Notification(
        issue_id=new_issue.id,
        type=NotificationType.ISSUE_CREATED.value,
        message=f"Your report #{new_issue.id} has been submitted and assigned to {dept_label}",
        citizen_token=tracking_token
    )
    db.add(notification)
    
    # Add duplicate notification if detected
    if duplicate_of:
        dup_message = (
            f"A similar issue #{duplicate_of} already exists at the same location. Your report has been linked as a duplicate."
            if is_definite_duplicate
            else f"A similar issue #{duplicate_of} was found. Your report has still been recorded."
        )
        dup_notification = Notification(
            issue_id=new_issue.id,
            type=NotificationType.DUPLICATE_DETECTED.value,
            message=dup_message,
            citizen_token=tracking_token
        )
        db.add(dup_notification)
    
    db.commit()

    # 13. Send email to department officials (async-friendly, non-blocking)
    try:
        notify_new_issue(new_issue)
    except Exception as e:
        print(f"Email notification failed: {e}")

    # Return response with tracking token
    return IssueCreateResponse.from_issue(new_issue, tracking_token, duplicate_of)


@router.get("/", response_model=List[IssueResponse])
def read_issues(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    issues = crud_issue.get_issues(db, skip=skip, limit=limit)
    return issues


@router.get("/{issue_id}", response_model=IssueResponse)
def read_issue(issue_id: int, db: Session = Depends(get_db)):
    db_issue = crud_issue.get_issue(db, issue_id=issue_id)
    if db_issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return db_issue


@router.get("/{issue_id}/duplicates", response_model=List[IssueResponse])
def get_duplicates(
    issue_id: int,
    threshold: float = 0.85,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """
    Find visually similar issues based on image embeddings.
    Returns issues above the similarity threshold.
    """
    # Get the original issue
    db_issue = crud_issue.get_issue(db, issue_id=issue_id)
    if db_issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Generate embedding from the stored image
    embedding = clip_service.get_embedding(db_issue.image_url)
    if embedding is None:
        raise HTTPException(status_code=500, detail="Could not generate embedding for this issue")

    # Search for similar
    similar = faiss_manager.search_similar(embedding, threshold=threshold, k=limit + 1)

    # Filter out the issue itself and fetch from DB
    duplicate_ids = [sim_id for sim_id, _ in similar if sim_id != issue_id][:limit]

    duplicates = []
    for dup_id in duplicate_ids:
        dup_issue = crud_issue.get_issue(db, issue_id=dup_id)
        if dup_issue:
            duplicates.append(dup_issue)

    return duplicates


@router.patch("/{issue_id}/status", response_model=IssueResponse)
def update_issue_status(
    issue_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update the status of an issue (e.g., Open -> Resolved).
    In a real app, this would verify admin role first.
    """
    # Validate status value
    valid_statuses = ["Open", "Resolved", "In Progress", "Closed"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Get the issue first to access citizen_token
    db_issue = crud_issue.get_issue(db, issue_id)
    if not db_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Update the issue
    updated_issue = crud_issue.update_status(db, issue_id, status_update.status)
    
    # Create notification for citizen if they have a tracking token
    if db_issue.citizen_token:
        if status_update.status == "Resolved":
            notification_type = NotificationType.ISSUE_RESOLVED.value
            message = f"Great news! Your issue #{issue_id} has been resolved. Thank you for helping improve our city!"
        elif status_update.status == "In Progress":
            notification_type = NotificationType.STATUS_UPDATED.value
            message = f"Your issue #{issue_id} is now being worked on. Status: In Progress"
        else:
            notification_type = NotificationType.STATUS_UPDATED.value
            message = f"Your issue #{issue_id} status has been updated to: {status_update.status}"
        
        notification = Notification(
            issue_id=issue_id,
            type=notification_type,
            message=message,
            citizen_token=db_issue.citizen_token
        )
        db.add(notification)
        db.commit()
    
    # Send legacy console notification
    if status_update.status == "Resolved":
        notify_issue_resolved(issue_id)
    elif status_update.status == "Open":
        notify_issue_reopened(issue_id)
    
    return updated_issue
