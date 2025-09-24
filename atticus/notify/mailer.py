"""SMTP mailer for escalation emails.

Reads SMTP_* and CONTACT_EMAIL from AppSettings (which sources .env).

Exports:
    send_escalation(subject, body, to=None)
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from atticus.config import load_settings
from atticus.logging import configure_logging


def _compose_message(subject: str, body: str, sender: str, recipient: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)
    return msg


def send_escalation(subject: str, body: str, to: str | None = None) -> None:
    """Send an escalation email via SMTP.

    Recipient resolution order: explicit `to` -> `SMTP_TO` -> `CONTACT_EMAIL`.
    No-op if no recipient or SMTP host configured.
    """
    settings = load_settings()
    logger = configure_logging(settings)

    recipient = (to or settings.smtp_to or settings.contact_email or "").strip()
    if not recipient:
        logger.warning("No recipient configured for escalation email; skipping send")
        return

    host = (settings.smtp_host or "").strip()
    if not host:
        logger.warning("SMTP_HOST not configured; skipping send")
        return

    port = int(settings.smtp_port or 587)
    sender = settings.smtp_from or settings.smtp_user or f"no-reply@{host}"

    msg = _compose_message(subject=subject, body=body, sender=sender, recipient=recipient)

    if settings.smtp_dry_run:
        logger.info(
            "escalation_email_dry_run",
            extra={"extra_payload": {"to": "(redacted)", "host": host, "port": port}},
        )
        return {"status": "dry-run", "host": host, "port": port}

    client = smtplib.SMTP(host, port)
    try:
        # STARTTLS as per security guidance
        client.starttls()
        if settings.smtp_user and settings.smtp_pass:
            client.login(settings.smtp_user, settings.smtp_pass)
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
    finally:
        try:
            client.quit()
        except Exception:
            pass
