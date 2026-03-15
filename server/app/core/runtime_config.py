"""
Runtime Config Store for AdvoLens

Holds mail mode, SMTP credentials, and per-department emails entirely in memory.
No DB, no restart needed.

⚠️ MEMORY-ONLY — all values are cleared on server restart.
DB persistence is deferred to a future migration sprint.
"""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger("advolens.runtime_config")

# Default configuration — seeded from environment variables on startup
_config: Dict[str, Any] = {
    "mail_mode": os.getenv("MAIL_MODE", "mock"),  # "mock" | "smtp"
    "smtp": {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_EMAIL", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_address": os.getenv("SMTP_EMAIL", ""),
    },
    "dept_emails": {
        "municipality": os.getenv("EMAIL_MUNICIPALITY", ""),
        "pwd": os.getenv("EMAIL_PWD", ""),
        "kseb": os.getenv("EMAIL_KSEB", ""),
        "water_authority": os.getenv("EMAIL_WATER_AUTHORITY", ""),
        "other": os.getenv("EMAIL_OTHER", ""),
    },
}

# In-memory mock mail log
_mock_mail_log = []
_mock_mail_counter = 0


# ── Getters ──────────────────────────────────────────────────────────────────

def get_mail_mode() -> str:
    return _config["mail_mode"]


def get_smtp_config() -> Dict[str, Any]:
    return dict(_config["smtp"])


def get_dept_emails() -> Dict[str, str]:
    return dict(_config["dept_emails"])


def get_dept_email(dept: str) -> str:
    return _config["dept_emails"].get(dept, "")


def get_full_config() -> Dict[str, Any]:
    """Return full config with SMTP password masked."""
    smtp = dict(_config["smtp"])
    smtp["password"] = "••••••••" if smtp.get("password") else ""
    return {
        "mail_mode": _config["mail_mode"],
        "smtp": smtp,
        "dept_emails": dict(_config["dept_emails"]),
    }


# ── Setters ──────────────────────────────────────────────────────────────────

def set_mail_mode(mode: str) -> None:
    if mode not in ("mock", "smtp"):
        raise ValueError(f"Invalid mail_mode: {mode!r}. Must be 'mock' or 'smtp'.")
    _config["mail_mode"] = mode
    logger.info("Mail mode changed to: %s", mode)


def set_smtp_config(host: str, port: int, username: str, password: str, from_address: str) -> None:
    _config["smtp"] = {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_address": from_address,
    }
    logger.info("SMTP config updated (host=%s, port=%d, username=%s)", host, port, username)


def set_dept_email(dept: str, email: str) -> None:
    _config["dept_emails"][dept] = email
    logger.info("Department email updated: %s → %s", dept, email)


# ── Mock Mail Log ─────────────────────────────────────────────────────────────

def append_mock_mail(to: str, subject: str, html_body: str, dept: str, issue_id: int) -> Dict[str, Any]:
    global _mock_mail_counter
    _mock_mail_counter += 1
    from datetime import datetime, timezone
    entry = {
        "id": _mock_mail_counter,
        "to": to,
        "subject": subject,
        "html_body": html_body,
        "department": dept,
        "issue_id": issue_id,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "mock_delivered",
    }
    _mock_mail_log.insert(0, entry)  # newest first
    return entry


def get_mock_mails() -> list:
    return list(_mock_mail_log)


def get_mock_mail_by_id(mail_id: int) -> Dict[str, Any] | None:
    for entry in _mock_mail_log:
        if entry["id"] == mail_id:
            return entry
    return None


def clear_mock_mails() -> None:
    _mock_mail_log.clear()
    logger.info("Mock mail log cleared.")
