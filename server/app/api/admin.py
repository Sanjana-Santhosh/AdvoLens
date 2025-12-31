from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole, Department
from app.models.issue import Issue
from app.schemas.issue import IssueResponse

router = APIRouter(tags=["admin"])


class ReassignRequest(BaseModel):
    department: Department


class DepartmentStats(BaseModel):
    department: str
    total: int
    open: int
    resolved: int


@router.get("/issues", response_model=List[IssueResponse])
def get_admin_issues(
    status_filter: Optional[str] = None,
    department_filter: Optional[Department] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get issues based on user role:
    - Super Admin: sees all issues
    - Official: sees only their department's issues
    """
    query = db.query(Issue)
    
    # LOGIC: Filter based on Role
    if current_user.role == UserRole.OFFICIAL:
        # Officials ONLY see their department's issues
        if current_user.department:
            query = query.filter(Issue.department == current_user.department)
        else:
            # Official without department sees nothing
            return []
    
    # Super Admin sees everything (no role-based filter applied)
    
    # Apply optional filters
    if status_filter:
        query = query.filter(Issue.status == status_filter)
    
    if department_filter and current_user.role == UserRole.SUPER_ADMIN:
        # Only super admin can filter by any department
        query = query.filter(Issue.department == department_filter)
    
    # Order by newest first
    query = query.order_by(Issue.created_at.desc())
    
    return query.all()


@router.patch("/{issue_id}/reassign", response_model=IssueResponse)
def reassign_issue(
    issue_id: int,
    reassign_data: ReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reassign an issue to a different department.
    Only Super Admins can reassign issues.
    """
    # ONLY Super Admin can reassign
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can reassign issues"
        )
    
    # Find the issue
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Update department
    issue.department = reassign_data.department
    db.commit()
    db.refresh(issue)
    
    return issue


@router.delete("/{issue_id}")
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an issue (e.g., spam entries).
    Only Super Admins can delete issues.
    """
    # ONLY Super Admin can delete
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can delete issues"
        )
    
    # Find and delete the issue
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    db.delete(issue)
    db.commit()
    
    return {"message": "Issue deleted successfully", "id": issue_id}


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for the admin dashboard.
    """
    query = db.query(Issue)
    
    # Filter for officials
    if current_user.role == UserRole.OFFICIAL and current_user.department:
        query = query.filter(Issue.department == current_user.department)
    
    issues = query.all()
    
    total = len(issues)
    open_count = sum(1 for i in issues if i.status == "Open")
    resolved_count = sum(1 for i in issues if i.status == "Resolved")
    in_progress_count = sum(1 for i in issues if i.status == "In Progress")
    
    # Department breakdown (only for super admin)
    dept_stats = []
    if current_user.role == UserRole.SUPER_ADMIN:
        for dept in Department:
            dept_issues = [i for i in issues if i.department == dept]
            dept_stats.append({
                "department": dept.value,
                "total": len(dept_issues),
                "open": sum(1 for i in dept_issues if i.status == "Open"),
                "resolved": sum(1 for i in dept_issues if i.status == "Resolved")
            })
    
    return {
        "total": total,
        "open": open_count,
        "resolved": resolved_count,
        "in_progress": in_progress_count,
        "department_stats": dept_stats if dept_stats else None,
        "user_department": current_user.department.value if current_user.department else None,
        "user_role": current_user.role.value
    }
