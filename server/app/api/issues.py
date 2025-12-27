from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os

from app.core.database import get_db
from app.schemas.issue import IssueResponse
from app.crud import issue as crud_issue
from app.ml.clip_service import clip_service
from app.ml.faiss_manager import faiss_manager


router = APIRouter(tags=["issues"])

# Directory to save uploaded images locally (for now)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=IssueResponse)
async def create_issue(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    lat: float = Form(...),
    lon: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Save the image file locally
    file_location = f"{UPLOAD_DIR}/{image.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(image.file, file_object)

    # 2. Generate Embedding
    embedding = clip_service.get_embedding(file_location)

    # 3. Check for Visual Duplicates
    if embedding is not None:
        similar_issues = faiss_manager.search_similar(embedding, threshold=0.92)
        if similar_issues:
            original_id, score = similar_issues[0]
            print(f"Duplicate detected! Similar to Issue #{original_id} with score {score}")
            # Optionally: raise HTTPException here to block creation

    # 4. Save to DB
    new_issue = crud_issue.create_issue(
        db=db,
        title=title,
        description=description,
        image_url=file_location,
        lat=lat,
        lon=lon,
    )

    # 5. Add to Faiss Index for future searches
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
