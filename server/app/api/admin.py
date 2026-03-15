from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.core import runtime_config as cfg
from app.models.user import User, UserRole, Department
from app.models.issue import Issue
from app.schemas.issue import IssueResponse
from app.services.email_service import send_email

router = APIRouter(tags=["admin"])


class ReassignRequest(BaseModel):
    department: Department


class DepartmentStats(BaseModel):
    department: str
    total: int
    open: int
    resolved: int


class MailModeRequest(BaseModel):
    mode: str  # "mock" | "smtp"


class SmtpConfigRequest(BaseModel):
    host: str
    port: int = 587
    username: str
    password: str
    from_address: str


class DeptEmailRequest(BaseModel):
    email: str


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


# ── Mail Config Endpoints (Super Admin only) ──────────────────────────────────

def _require_super_admin(current_user: User) -> None:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can manage email settings",
        )


@router.get("/mail-config")
def get_mail_config(current_user: User = Depends(get_current_user)):
    """Return current mail config with SMTP password masked."""
    _require_super_admin(current_user)
    return cfg.get_full_config()


@router.put("/mail-config/mode")
def set_mail_mode(
    body: MailModeRequest,
    current_user: User = Depends(get_current_user),
):
    """Toggle between mock and SMTP mail mode."""
    _require_super_admin(current_user)
    try:
        cfg.set_mail_mode(body.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"mail_mode": cfg.get_mail_mode()}


@router.put("/mail-config/smtp")
def update_smtp_config(
    body: SmtpConfigRequest,
    current_user: User = Depends(get_current_user),
):
    """Update SMTP credentials. ⚠️ memory-only — cleared on restart."""
    _require_super_admin(current_user)
    cfg.set_smtp_config(
        host=body.host,
        port=body.port,
        username=body.username,
        password=body.password,
        from_address=body.from_address,
    )
    result = cfg.get_full_config()
    result["note"] = "⚠️ memory-only — cleared on restart"
    return result


@router.post("/mail-config/test")
def send_test_email(current_user: User = Depends(get_current_user)):
    """Send a test email to the super admin's own address."""
    _require_super_admin(current_user)
    recipient = current_user.email
    if not recipient:
        raise HTTPException(status_code=400, detail="Super admin has no email address on record")
    subject = "[AdvoLens] Test Email — Mail Config OK"
    body = (
        "<h2>✅ AdvoLens Email Test</h2>"
        "<p>Your email configuration is working correctly.</p>"
        f"<p><strong>Mode:</strong> {cfg.get_mail_mode()}</p>"
    )
    ok = send_email(recipient, subject, body)
    return {"sent": ok, "recipient": recipient, "mode": cfg.get_mail_mode()}


@router.put("/dept-emails/{dept}")
def update_dept_email(
    dept: str,
    body: DeptEmailRequest,
    current_user: User = Depends(get_current_user),
):
    """Update the alert email for a department. ⚠️ memory-only — cleared on restart."""
    _require_super_admin(current_user)
    valid_depts = {"municipality", "pwd", "kseb", "water_authority", "other"}
    if dept not in valid_depts:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department. Must be one of: {', '.join(sorted(valid_depts))}",
        )
    cfg.set_dept_email(dept, body.email)
    return {
        "department": dept,
        "email": body.email,
        "note": "⚠️ memory-only — cleared on restart",
    }


# ── Mock Mail Log Endpoints (Super Admin only) ────────────────────────────────

@router.get("/mock-mails")
def list_mock_mails(current_user: User = Depends(get_current_user)):
    """Return the full mock mail log, newest first (no HTML body)."""
    _require_super_admin(current_user)
    mails = cfg.get_mock_mails()
    # Strip html_body for list view to keep response small
    return [
        {k: v for k, v in m.items() if k != "html_body"}
        for m in mails
    ]


@router.get("/mock-mails/{mail_id}")
def get_mock_mail(mail_id: int, current_user: User = Depends(get_current_user)):
    """Return a single mock mail entry with full HTML body."""
    _require_super_admin(current_user)
    entry = cfg.get_mock_mail_by_id(mail_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Mock mail not found")
    return entry


@router.delete("/mock-mails")
def clear_mock_mails(current_user: User = Depends(get_current_user)):
    """Clear the mock mail log."""
    _require_super_admin(current_user)
    cfg.clear_mock_mails()
    return {"message": "Mock mail log cleared"}
