"""SMTP mailer for escalation emails.

Reads SMTP_* and CONTACT_EMAIL from AppSettings (which sources .env).

Exports:
    send_escalation(subject, body, to=None)
"""

from __future__ import annotations

import smtplib
from collections.abc import Sequence
from email.message import EmailMessage

from atticus.config import load_settings
from atticus.logging import configure_logging


def _compose_message(
    subject: str,
    body: str,
    sender: str,
    recipients: Sequence[str],
    cc: Sequence[str] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.set_content(body)
    return msg


def send_escalation(
    subject: str,
    body: str,
    to: str | Sequence[str] | None = None,
    cc: Sequence[str] | None = None,
) -> dict[str, object] | None:
    """Send an escalation email via SMTP.

    Recipient resolution order: explicit `to` -> `SMTP_TO` -> `CONTACT_EMAIL`.
    No-op if no recipient or SMTP host configured.
    """
    settings = load_settings()
    logger = configure_logging(settings)

    if isinstance(to, str):
        recipients = [to] if to.strip() else []
    elif to is None:
        default_recipient = settings.smtp_to or settings.contact_email or ""
        recipients = [default_recipient.strip()] if default_recipient and default_recipient.strip() else []
    else:
        recipients = [value.strip() for value in to if value and value.strip()]

    if not recipients:
        logger.warning("No recipient configured for escalation email; skipping send")
        return None

    host = (settings.smtp_host or "").strip()
    if not host:
        logger.warning("SMTP_HOST not configured; skipping send")
        return None

    port = int(settings.smtp_port or 587)
    sender = settings.smtp_from or settings.smtp_user or f"no-reply@{host}"

    cc_list = [value.strip() for value in (cc or []) if value and value.strip()]
    msg = _compose_message(subject=subject, body=body, sender=sender, recipients=recipients, cc=cc_list)

    if settings.smtp_dry_run:
        logger.info(
            "escalation_email_dry_run",
            extra={
                "extra_payload": {
                    "to": "(redacted)",
                    "cc": ["(redacted)"] if cc_list else [],
                    "host": host,
                    "port": port,
                }
            },
        )
        return {"status": "dry-run", "host": host, "port": port}

    client = smtplib.SMTP(host, port)
    try:
        # STARTTLS as per security guidance
        client.starttls()
        if settings.smtp_user and settings.smtp_pass:
            client.login(settings.smtp_user, settings.smtp_pass)
        recipients_all = list(recipients)
        if cc_list:
            recipients_all.extend(cc_list)
        client.sendmail(sender, recipients_all, msg.as_string())
        logger.info(
            "escalation_email_sent",
            extra={
                "extra_payload": {
                    "to": "(redacted)",
                    "cc": ["(redacted)"] if cc_list else [],
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
    return None
