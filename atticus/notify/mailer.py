"""SMTP mailer for escalation emails.

Reads SMTP_* and CONTACT_EMAIL from AppSettings (which sources .env).

Exports:
    send_escalation(subject, body, to=None)
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Literal, TypedDict

from atticus.config import load_settings
from atticus.logging import configure_logging, log_error


class EscalationDeliveryError(RuntimeError):
    """Raised when an escalation email cannot be delivered."""

    def __init__(self, message: str, *, reason: str = "unknown") -> None:
        super().__init__(message)
        self.reason = reason


class _DryRunResult(TypedDict):
    status: Literal["dry-run"]
    host: str
    port: int


def _compose_message(subject: str, body: str, sender: str, recipient: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)
    return msg


def _log_failure(logger, *, reason: str, host: str, port: int, exc: Exception) -> None:
    log_error(
        logger,
        "escalation_email_failed",
        reason=reason,
        host=host,
        port=port,
        error=str(exc),
    )


def send_escalation(subject: str, body: str, to: str | None = None) -> _DryRunResult | None:
    """Send an escalation email via SMTP.

    Recipient resolution order: explicit `to` -> `SMTP_TO` -> `CONTACT_EMAIL`.
    Returns dry-run metadata when SMTP_DRY_RUN is enabled; otherwise None.
    """
    settings = load_settings()
    logger = configure_logging(settings)

    recipient = (to or settings.smtp_to or settings.contact_email or "").strip()
    if not recipient:
        logger.warning("No recipient configured for escalation email; skipping send")
        return None

    host = (settings.smtp_host or "").strip()
    if not host:
        logger.warning("SMTP_HOST not configured; skipping send")
        return None

    port = int(settings.smtp_port or 587)
    sender = settings.smtp_from or settings.smtp_user or f"no-reply@{host}"

    msg = _compose_message(subject=subject, body=body, sender=sender, recipient=recipient)

    if settings.smtp_dry_run:
        logger.info(
            "escalation_email_dry_run",
            extra={"extra_payload": {"to": "(redacted)", "host": host, "port": port}},
        )
        return {"status": "dry-run", "host": host, "port": int(port)}

    try:
        with smtplib.SMTP(host, port, timeout=20) as client:
            client.ehlo()
            try:
                client.starttls()
            except smtplib.SMTPNotSupportedError as exc:  # pragma: no cover - legacy SMTP
                _log_failure(logger, reason="tls_not_supported", host=host, port=port, exc=exc)
                raise EscalationDeliveryError(
                    "SMTP server does not support STARTTLS; escalation email not sent.",
                    reason="tls_not_supported",
                ) from exc

            if settings.smtp_user and settings.smtp_pass:
                client.login(settings.smtp_user, settings.smtp_pass)

            try:
                client.send_message(msg)
            except AttributeError:
                client.sendmail(sender, [recipient], msg.as_string())

            logger.info(
                "escalation_email_sent",
                extra={
                    "extra_payload": {
                        "to": "(redacted)",
                        "host": host,
                        "port": port,
                    }
                },
            )
    except smtplib.SMTPAuthenticationError as exc:
        _log_failure(logger, reason="authentication_failed", host=host, port=port, exc=exc)
        raise EscalationDeliveryError(
            "SMTP authentication failed while sending escalation email.",
            reason="authentication_failed",
        ) from exc
    except (smtplib.SMTPConnectError, OSError) as exc:
        _log_failure(logger, reason="connection_error", host=host, port=port, exc=exc)
        raise EscalationDeliveryError(
            "Unable to connect to the SMTP server for escalation email.",
            reason="connection_error",
        ) from exc
    except smtplib.SMTPException as exc:
        _log_failure(logger, reason="smtp_error", host=host, port=port, exc=exc)
        raise EscalationDeliveryError(
            "Unexpected SMTP error while sending escalation email.",
            reason="smtp_error",
        ) from exc

    return None
