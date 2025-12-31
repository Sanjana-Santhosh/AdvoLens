from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os

from app.core.database import get_db
from app.schemas.issue import IssueResponse
from app.crud import issue as crud_issue
from app.ml.clip_service import clip_service
from app.ml.faiss_manager import faiss_manager
from app.ml.gemini_service import gemini_service
from app.services.notification import notify_issue_resolved, notify_issue_reopened
from app.services.routing_service import assign_department
from app.services.cloudinary_service import upload_image


router = APIRouter(tags=["issues"])

# Use /tmp for temporary files (works on Render)
TEMP_DIR = "/tmp"


class StatusUpdate(BaseModel):
    """Schema for updating issue status"""
    status: str


@router.post("/", response_model=IssueResponse)
async def create_issue(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    lat: float = Form(...),
    lon: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Save temp file (use /tmp for Render compatibility)
    temp_path = f"{TEMP_DIR}/{image.filename}"
    with open(temp_path, "wb+") as file_object:
        shutil.copyfileobj(image.file, file_object)

    # 2. Upload to Cloudinary
    cloud_url = upload_image(temp_path)
    if not cloud_url:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail="Image upload failed")

    # 3. AI Analysis (CLIP for embeddings, Gemini for captioning)
    embedding = clip_service.get_embedding(temp_path)
    gemini_result = gemini_service.analyze_image(temp_path)

    # 4. Clean up temp file
    os.remove(temp_path)

    # 5. Check for Visual Duplicates
    if embedding is not None:
        similar_issues = faiss_manager.search_similar(embedding, threshold=0.92)
        if similar_issues:
            original_id, score = similar_issues[0]
            print(f"⚠️ Duplicate detected! Similar to Issue #{original_id} with score {score:.3f}")
            # Optionally: raise HTTPException here to block creation

    # 6. AUTO-ASSIGN DEPARTMENT based on AI tags
    assigned_dept = assign_department(gemini_result.get('tags', []))
    print(f"🏛️ Auto-assigned to department: {assigned_dept.value}")

    # 7. Save to DB with Cloudinary URL
    new_issue = crud_issue.create_issue(
        db=db,
        title=title or gemini_result.get('caption'),  # Use AI caption if no title
        description=description,
        image_url=cloud_url,  # Now it's a full Cloudinary URL!
        caption=gemini_result.get('caption'),
        tags=gemini_result.get('tags'),
        lat=lat,
        lon=lon,
        department=assigned_dept,  # Save assigned department
    )

    # 8. Add to Faiss Index for future searches
    if embedding is not None:
        faiss_manager.add_vector(embedding, new_issue.id)

    return new_issue


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
    
    # Update the issue
    updated_issue = crud_issue.update_status(db, issue_id, status_update.status)
    if not updated_issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Send notification based on new status
    if status_update.status == "Resolved":
        notify_issue_resolved(issue_id)
    elif status_update.status == "Open":
        notify_issue_reopened(issue_id)
    
    return updated_issue
