"""
Notification Service for AdvoLens

This module handles sending notifications to users when their issues are updated.
Currently implements a simple console logger, but can be extended to support:
- Email (SMTP)
- Push notifications (Firebase)
- SMS (Twilio)
"""

from datetime import datetime


def send_notification(user_id: int, message: str, notification_type: str = "status_update"):
    """
    Send a notification to a user.
    
    In a real deployment, this would integrate with:
    - Firebase Cloud Messaging for push notifications
    - SMTP for email notifications
    - Twilio for SMS
    
    For now, we log to console for demo purposes.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "="*60)
    print(f"[NOTIFICATION SERVICE] {timestamp}")
    print(f"Type: {notification_type}")
    print(f"To User ID: {user_id}")
    print(f"Message: {message}")
    print("="*60 + "\n")
    
    # TODO: Implement real notification channels
    # Example for email:
    # send_email(user_email, subject, message)
    
    # Example for Firebase:
    # send_push_notification(user_fcm_token, title, message)
    
    return True


def notify_issue_resolved(issue_id: int, user_id: int = 1):
    """Notify user that their issue has been resolved."""
    message = f"Great news! Your issue #{issue_id} has been marked as Resolved. Thank you for helping keep our city clean!"
    return send_notification(user_id, message, "issue_resolved")


def notify_issue_reopened(issue_id: int, user_id: int = 1):
    """Notify user that their issue has been reopened."""
    message = f"Your issue #{issue_id} has been reopened for further investigation."
    return send_notification(user_id, message, "issue_reopened")


def notify_issue_created(issue_id: int, user_id: int = 1):
    """Notify user that their issue has been successfully created."""
    message = f"Your issue #{issue_id} has been successfully submitted and is being reviewed."
    return send_notification(user_id, message, "issue_created")
