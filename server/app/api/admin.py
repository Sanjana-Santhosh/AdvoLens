from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel
import os
import secrets

from app.core.database import get_db
from app.core.security import get_current_user
from app.core import runtime_config as cfg
from app.models.user import User, UserRole, Department
from app.models.issue import Issue
from app.models.engagement import Vote, Comment
from app.models.notification import Notification
from app.ml.clip_service import clip_service
from app.ml.faiss_manager import INDEX_FILE, METADATA_FILE, faiss_manager
from app.core.ml_debug_log import (
    MAX_ML_DEBUG_LOGS,
    clear_ml_debug_logs,
    get_ml_debug_log_count,
    get_ml_debug_logs,
)
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


class ClearDbRequest(BaseModel):
    confirm_phrase: str
    include_users: bool = True
    preserve_seeded_data: bool = True
    purge_vector_files: bool = True


maintenance_basic = HTTPBasic(auto_error=False)

SEEDED_USER_EMAILS = {
    "admin@advolens.com",
    "municipality@advolens.com",
    "pwd@advolens.com",
    "kseb@advolens.com",
    "water@advolens.com",
    "admin@advolens.gov",
    "municipality@advolens.gov",
    "pwd@advolens.gov",
    "kseb@advolens.gov",
    "water@advolens.gov",
}

SEEDED_ISSUE_TITLES = {
    "Garbage pile on MG Road",
    "Pothole on Highway",
    "Broken Streetlight",
    "Water Pipeline Leak",
}


def require_maintenance_basic_auth(
    credentials: Optional[HTTPBasicCredentials] = Depends(maintenance_basic),
) -> str:
    """
    Extra safety layer for dangerous maintenance endpoints.
    Bypassed by default while AUTH_DISABLED=true (or unset).
    Set AUTH_DISABLED=false to enforce this check, then configure
    MAINTENANCE_BASIC_USER and MAINTENANCE_BASIC_PASS in env.
    """
    if os.getenv("AUTH_DISABLED", "true").lower() in {"1", "true", "yes", "on"}:
        return "auth_disabled"

    expected_user = os.getenv("MAINTENANCE_BASIC_USER")
    expected_pass = os.getenv("MAINTENANCE_BASIC_PASS")

    if not expected_user or not expected_pass:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maintenance basic auth is not configured on server",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing maintenance credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    is_valid = (
        secrets.compare_digest(credentials.username, expected_user)
        and secrets.compare_digest(credentials.password, expected_pass)
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid maintenance credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


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


@router.delete("/{issue_id:int}")
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


@router.get("/ml-debug-logs")
def list_ml_debug_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Return latest in-memory ML debug logs (newest first).
    Retains only the last 100 entries.
    """
    _require_super_admin(current_user)
    safe_limit = max(1, min(limit, MAX_ML_DEBUG_LOGS))
    return {
        "total": get_ml_debug_log_count(),
        "limit": safe_limit,
        "max_retention": MAX_ML_DEBUG_LOGS,
        "logs": get_ml_debug_logs(limit=safe_limit),
    }


@router.delete("/ml-debug-logs")
def clear_ml_logs(current_user: User = Depends(get_current_user)):
    """Clear in-memory ML debug logs."""
    _require_super_admin(current_user)
    clear_ml_debug_logs()
    return {"message": "ML debug logs cleared"}


# ── Maintenance Endpoints (Super Admin + Basic Auth) ─────────────────────────

@router.post("/maintenance/rebuild-faiss")
def rebuild_faiss_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: str = Depends(require_maintenance_basic_auth),
):
    """
    Rebuild the Faiss index from current DB issues.
    Uses issue image URLs to regenerate embeddings.
    """
    _require_super_admin(current_user)

    issues = db.query(Issue).filter(Issue.image_url.isnot(None)).all()

    # Reset in-memory index first, then persist once at the end.
    faiss_manager.reset_index(persist=False)

    indexed = 0
    skipped = 0
    for issue in issues:
        embedding = clip_service.get_embedding(issue.image_url)
        if embedding is None:
            skipped += 1
            continue
        faiss_manager.add_vector(embedding, issue.id, persist=False)
        indexed += 1

    faiss_manager.save_index()

    return {
        "message": "Faiss index rebuilt",
        "total_issues": len(issues),
        "indexed": indexed,
        "skipped": skipped,
        "index_size": int(faiss_manager.index.ntotal),
    }


@router.post("/maintenance/clear-db")
def clear_database_data(
    body: ClearDbRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: str = Depends(require_maintenance_basic_auth),
):
    """
    Danger zone: clears application data from DB.
    Requires confirm_phrase == "DELETE ALL DATA".
    Set preserve_seeded_data=false for a true full wipe.
    """
    _require_super_admin(current_user)

    if body.confirm_phrase != "DELETE ALL DATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid confirm_phrase. Use exactly: "DELETE ALL DATA"',
        )

    deleted_counts: dict[str, int] = {}
    preserved_counts: dict[str, int] = {}
    try:
        comments_query = db.query(Comment)
        votes_query = db.query(Vote)
        notifications_query = db.query(Notification)
        issues_query = db.query(Issue)

        seeded_issue_ids: list[int] = []
        if body.preserve_seeded_data:
            seeded_issues_query = db.query(Issue).filter(
                or_(
                    Issue.citizen_token.like("demo_token_%"),
                    Issue.title.in_(SEEDED_ISSUE_TITLES),
                )
            )
            seeded_issue_ids = [issue.id for issue in seeded_issues_query.all()]
            preserved_counts["issues"] = len(seeded_issue_ids)

            if seeded_issue_ids:
                comments_query = comments_query.filter(~Comment.issue_id.in_(seeded_issue_ids))
                votes_query = votes_query.filter(~Vote.issue_id.in_(seeded_issue_ids))
                notifications_query = notifications_query.filter(~Notification.issue_id.in_(seeded_issue_ids))
                issues_query = issues_query.filter(~Issue.id.in_(seeded_issue_ids))
        else:
            preserved_counts["issues"] = 0

        deleted_counts["comments"] = comments_query.count()
        comments_query.delete(synchronize_session=False)

        deleted_counts["votes"] = votes_query.count()
        votes_query.delete(synchronize_session=False)

        deleted_counts["notifications"] = notifications_query.count()
        notifications_query.delete(synchronize_session=False)

        deleted_counts["issues"] = issues_query.count()
        issues_query.delete(synchronize_session=False)

        if body.include_users:
            users_query = db.query(User)
            if body.preserve_seeded_data:
                users_query = users_query.filter(~User.email.in_(SEEDED_USER_EMAILS))
            deleted_counts["users"] = users_query.count()
            users_query.delete(synchronize_session=False)
            if body.preserve_seeded_data:
                preserved_counts["seeded_users"] = db.query(User).filter(User.email.in_(SEEDED_USER_EMAILS)).count()
            else:
                preserved_counts["seeded_users"] = 0
        else:
            deleted_counts["users"] = 0
            if body.preserve_seeded_data:
                preserved_counts["seeded_users"] = db.query(User).filter(User.email.in_(SEEDED_USER_EMAILS)).count()
            else:
                preserved_counts["seeded_users"] = 0

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear database: {exc}",
        )

    # Keep search/index state aligned with cleared DB.
    faiss_manager.reset_index(persist=False)

    purged_vector_files: list[str] = []
    if body.purge_vector_files:
        for vector_file in (INDEX_FILE, METADATA_FILE):
            if os.path.exists(vector_file):
                os.remove(vector_file)
                purged_vector_files.append(vector_file)
    else:
        # Persist an empty index when disk purge is not requested.
        faiss_manager.save_index()

    cfg.clear_mock_mails()

    note = "Seeded users and seeded sample issues were preserved"
    if not body.preserve_seeded_data:
        note = "All records cleared (no seeded data preserved)"

    return {
        "message": "Database data cleared",
        "note": note,
        "include_users": body.include_users,
        "preserve_seeded_data": body.preserve_seeded_data,
        "purge_vector_files": body.purge_vector_files,
        "purged_vector_files": purged_vector_files,
        "deleted": deleted_counts,
        "preserved": preserved_counts,
    }
