"""Notification helpers (email escalation, etc.)."""

from .mailer import EscalationDeliveryError, send_escalation

__all__ = ["EscalationDeliveryError", "send_escalation"]
