"""Notification helpers (email escalation, etc.)."""

from .mailer import send_escalation

__all__ = ["send_escalation"]
