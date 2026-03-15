"""
Email Service for AdvoLens

Unified mock + SMTP email service.  Mail mode and credentials are read at
send-time from the runtime config store so that a toggle in the admin UI takes
effect on the very next submitted report — no restart required.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core import runtime_config as cfg
from app.services.email_templates import build_new_issue_email, build_status_change_email

logger = logging.getLogger("advolens.email")


# ── Low-level send ────────────────────────────────────────────────────────────

def _send_mock(recipient: str, subject: str, body: str, dept: str, issue_id: int) -> bool:
    """Append to in-memory log and print a structured console line."""
    cfg.append_mock_mail(
        to=recipient, subject=subject, html_body=body,
        dept=dept, issue_id=issue_id,
    )
    logger.info("[MOCK ✉️ ] #%d → %s | %s", issue_id, recipient, subject)
    return True


def _send_smtp(recipient: str, subject: str, body: str, issue_id: int) -> bool:
    """Send via smtplib using credentials from runtime config.

    Supports both SSL (port 465) and STARTTLS (port 587 or 25).
    """
    smtp = cfg.get_smtp_config()
    if not smtp.get("username") or not smtp.get("password"):
        logger.warning("[SMTP ⚠️ ] Credentials not set — skipping send to %s", recipient)
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp.get("from_address") or smtp["username"]
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    host = smtp["host"]
    port = smtp["port"]

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(smtp["username"], smtp["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(smtp["username"], smtp["password"])
                server.send_message(msg)
        logger.info("[SMTP ✅ ] Sent → %s | Issue #%d", recipient, issue_id)
        return True
    except Exception as exc:
        logger.error("[SMTP ❌ ] Failed → %s | %s", recipient, exc)
        return False


def _dispatch(recipient: str, subject: str, body: str, dept: str, issue_id: int) -> bool:
    """Route to mock or SMTP depending on current mail_mode."""
    if not recipient:
        logger.warning("[EMAIL ⚠️ ] No email configured for dept '%s' — skipping.", dept)
        return False

    if cfg.get_mail_mode() == "smtp":
        return _send_smtp(recipient, subject, body, issue_id)
    return _send_mock(recipient, subject, body, dept, issue_id)


# ── Public helpers ────────────────────────────────────────────────────────────

def notify_new_issue(issue) -> bool:
    """Send email notification when a new issue is created."""
    department_value = issue.department.value if hasattr(issue.department, "value") else str(issue.department)
    recipient = cfg.get_dept_email(department_value) or cfg.get_dept_email("other")

    # Extract lat/lon from PostGIS geometry if needed
    lat = lon = None
    try:
        lat = getattr(issue, "lat", None)
        lon = getattr(issue, "lon", None)
        if lat is None and hasattr(issue, "location") and issue.location is not None:
            from geoalchemy2.shape import to_shape
            pt = to_shape(issue.location)
            lon, lat = pt.x, pt.y
    except Exception:
        pass

    subject = f"[AdvoLens] New Issue — {issue.caption or f'Issue #{issue.id}'}"
    body = build_new_issue_email(
        issue_id=issue.id,
        caption=issue.caption or "",
        department=department_value,
        tags=issue.tags or [],
        lat=lat,
        lon=lon,
        image_url=issue.image_url,
    )
    return _dispatch(recipient, subject, body, department_value, issue.id)


def notify_issue_status_change(issue, new_status: str) -> bool:
    """Send email notification when issue status changes."""
    department_value = issue.department.value if hasattr(issue.department, "value") else str(issue.department)
    recipient = cfg.get_dept_email(department_value) or cfg.get_dept_email("other")

    status_emoji = {"Open": "🔴", "In Progress": "🟡", "Resolved": "✅", "Closed": "⬛"}.get(new_status, "📌")
    subject = f"{status_emoji} Issue #{issue.id} - Status: {new_status}"
    body = build_status_change_email(
        issue_id=issue.id,
        department=department_value,
        new_status=new_status,
        caption=issue.caption or "",
    )
    return _dispatch(recipient, subject, body, department_value, issue.id)


# ── Legacy thin wrappers kept for backwards-compat ────────────────────────────

def is_email_configured() -> bool:
    """True when SMTP credentials are set in runtime config."""
    smtp = cfg.get_smtp_config()
    return bool(smtp.get("username") and smtp.get("password"))


def send_email(recipient: str, subject: str, body: str) -> bool:
    """Low-level send respecting current mail_mode (no dept context)."""
    return _dispatch(recipient, subject, body, dept="other", issue_id=0)


def send_department_email(department: str, subject: str, body: str) -> bool:
    """Send to a department using runtime config addresses."""
    recipient = cfg.get_dept_email(department) or cfg.get_dept_email("other")
    return _dispatch(recipient, subject, body, dept=department, issue_id=0)
