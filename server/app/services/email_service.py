"""
Email Service for AdvoLens

This module handles sending email notifications to department officials
when new issues are assigned to them.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Department Email Mapping - Update these with real department emails
DEPT_EMAILS = {
    "municipality": os.getenv("EMAIL_MUNICIPALITY", "municipality@city.gov.in"),
    "water_authority": os.getenv("EMAIL_WATER_AUTHORITY", "water@city.gov.in"),
    "kseb": os.getenv("EMAIL_KSEB", "kseb@city.gov.in"),
    "pwd": os.getenv("EMAIL_PWD", "pwd@city.gov.in"),
    "other": os.getenv("EMAIL_OTHER", "admin@advolens.com")
}

# SMTP Configuration
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))


def is_email_configured() -> bool:
    """Check if email service is properly configured"""
    return bool(SMTP_EMAIL and SMTP_PASSWORD)


def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        recipient: Email address to send to
        subject: Email subject line
        body: HTML body of the email
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not is_email_configured():
        print("⚠️ Email not configured - skipping email send")
        print(f"   Would have sent to: {recipient}")
        print(f"   Subject: {subject}")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


def send_department_email(department: str, subject: str, body: str) -> bool:
    """Send email to the appropriate department"""
    recipient = DEPT_EMAILS.get(department, DEPT_EMAILS["other"])
    return send_email(recipient, subject, body)


def notify_new_issue(issue) -> bool:
    """
    Send email notification when a new issue is created.
    
    Args:
        issue: The Issue model instance
    
    Returns:
        True if email sent successfully
    """
    department_value = issue.department.value if hasattr(issue.department, 'value') else str(issue.department)
    tags_str = ', '.join(issue.tags) if issue.tags else 'None'
    
    subject = f"🚨 New {department_value.upper()} Issue #{issue.id}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .footer {{ background: #1f2937; color: white; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; }}
            .btn {{ background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; }}
            .tag {{ background: #e5e7eb; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">🚨 New Issue Reported</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Issue #{issue.id} - {department_value.replace('_', ' ').title()}</p>
            </div>
            <div class="content">
                <p><strong>Description:</strong></p>
                <p>{issue.caption or 'No description provided'}</p>
                
                <p><strong>Tags:</strong></p>
                <p>{''.join([f'<span class="tag">{tag}</span>' for tag in (issue.tags or [])])}</p>
                
                <p><strong>Location:</strong></p>
                <p><a href="https://maps.google.com/?q={issue.lat},{issue.lon}" target="_blank">📍 View on Google Maps</a></p>
                
                <p><strong>Image:</strong></p>
                <p><a href="{issue.image_url}" target="_blank">🖼️ View Photo</a></p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                
                <p style="text-align: center;">
                    <a href="https://advolens.vercel.app/admin/dashboard" class="btn">
                        Review in Dashboard →
                    </a>
                </p>
            </div>
            <div class="footer">
                <p style="margin: 0;">AdvoLens - Civic Issue Management</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_department_email(department_value, subject, body)


def notify_issue_status_change(issue, new_status: str) -> bool:
    """
    Send email notification when issue status changes.
    
    Args:
        issue: The Issue model instance
        new_status: The new status value
    
    Returns:
        True if email sent successfully
    """
    department_value = issue.department.value if hasattr(issue.department, 'value') else str(issue.department)
    
    status_emoji = {
        "Open": "🔴",
        "In Progress": "🟡",
        "Resolved": "✅",
        "Closed": "⬛"
    }.get(new_status, "📌")
    
    subject = f"{status_emoji} Issue #{issue.id} - Status: {new_status}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .status-badge {{ 
                display: inline-block; 
                padding: 8px 16px; 
                border-radius: 20px; 
                font-weight: bold;
                background: {'#dcfce7' if new_status == 'Resolved' else '#fef3c7' if new_status == 'In Progress' else '#fee2e2'};
                color: {'#166534' if new_status == 'Resolved' else '#92400e' if new_status == 'In Progress' else '#991b1b'};
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Issue #{issue.id} Status Updated</h2>
            <p><strong>New Status:</strong> <span class="status-badge">{status_emoji} {new_status}</span></p>
            <p><strong>Department:</strong> {department_value.replace('_', ' ').title()}</p>
            <p><strong>Description:</strong> {issue.caption or 'No description'}</p>
            <hr>
            <p><a href="https://advolens.vercel.app/admin/dashboard">View in Dashboard</a></p>
        </div>
    </body>
    </html>
    """
    
    return send_department_email(department_value, subject, body)
