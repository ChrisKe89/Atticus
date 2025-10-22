"""Database seeding utility used by the test suite and CLI."""

from __future__ import annotations

import argparse
import os
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

SEED_USERS = [
    {
        "id": "user-seed-author",
        "email": "glossary.author@seed.atticus",
        "name": "Glossary Seed Author",
        "role": "REVIEWER",
    },
    {
        "id": "user-seed-approver",
        "email": "glossary.approver@seed.atticus",
        "name": "Glossary Seed Approver",
        "role": "ADMIN",
    },
]

GLOSSARY_SEEDS = [
    {
        "id": "glossary-entry-managed-print-services",
        "term": "Managed Print Services",
        "definition": (
            "End-to-end management of printers, consumables, maintenance, and support "
            "delivered as a subscription."
        ),
        "synonyms": ["MPS", "Print-as-a-service"],
        "aliases": ["Managed Print"],
        "units": ["fleets"],
        "product_families": ["Enterprise Services"],
        "status": "APPROVED",
        "review_notes": "Approved for launch collateral and onboarding playbooks.",
        "reviewer_id": "user-seed-approver",
        "reviewed_at": "2024-05-01T12:00:00Z",
    },
    {
        "id": "glossary-entry-proactive-maintenance",
        "term": "Proactive Maintenance",
        "definition": (
            "Scheduled device inspections and firmware rollouts designed to prevent "
            "outages before they impact revenue teams."
        ),
        "synonyms": ["Preventative maintenance"],
        "aliases": ["Predictive maintenance"],
        "units": ["visits/year"],
        "product_families": ["Field Services"],
        "status": "PENDING",
    },
    {
        "id": "glossary-entry-toner-optimization",
        "term": "Toner Optimization",
        "definition": (
            "Adaptive print routing and toner yield tracking that reduce waste while "
            "maintaining SLA-compliant image quality."
        ),
        "synonyms": ["Smart toner", "Consumable optimisation"],
        "aliases": ["Toner yield optimization"],
        "units": ["pages"],
        "product_families": ["C7070", "C8180"],
        "status": "REJECTED",
        "review_notes": "Rejected pending customer-ready evidence and usage data.",
        "reviewer_id": "user-seed-approver",
        "reviewed_at": "2024-05-15T09:30:00Z",
    },
]

CHAT_SEEDS = [
    {
        "id": "chat-escalated-calibration",
        "question": (
            "Color calibration fails with streak artifacts on the ProLine 5100 series. "
            "What should we try next?"
        ),
        "confidence": 0.41,
        "status": "escalated",
        "request_id": "req-seed-002",
        "top_sources": [
            {
                "path": "content/troubleshooting/calibration-checklist.md#step-4",
                "score": 0.68,
                "heading": "Step 4 - Inspect rollers",
                "chunkId": "chunk-calibration-4",
            },
            {
                "path": "content/faq/pressroom-maintenance.md#color",
                "score": 0.62,
                "heading": "Color drift playbook",
                "chunkId": "chunk-maintenance-color",
            },
        ],
        "created_at": "2024-06-18T14:45:00Z",
        "audit_log": [
            {
                "action": "escalate",
                "at": "2024-06-18T15:00:00.000Z",
                "actorId": "user-seed-approver",
                "actorRole": "ADMIN",
                "summary": "Calibration streaks observed in pilot deployment.",
            },
        ],
        "user_id": "user-seed-author",
        "tickets": [
            {
                "id": "ticket-ae-1001",
                "key": "AE-1001",
                "status": "open",
                "assignee": "AEX-ops",
                "last_activity": "2024-06-18T15:00:00Z",
                "summary": "Investigate streak artifacts for ProLine 5100 pilot.",
                "audit_log": [
                    {
                        "action": "created",
                        "at": "2024-06-18T15:00:00.000Z",
                        "actorId": "user-seed-approver",
                        "actorRole": "ADMIN",
                    },
                ],
            },
        ],
    },
]


def _load_env_from_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key or key in os.environ:
            continue
        cleaned = value.strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1]
        os.environ[key] = cleaned


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _json(value: Any) -> Jsonb:
    return Jsonb(value)


def _normalize_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    sanitized = "".join(char for char in normalized if char.isalnum())
    return sanitized.lower()


def _normalize_family(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    compact = " ".join(normalized.replace("-", " ").split())
    return compact.upper()


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def seed_database(*, verbose: bool = False) -> None:
    _load_env_from_file(Path(".env"))
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set before running db:seed")

    org_id = os.environ.get("DEFAULT_ORG_ID", "org-atticus")
    org_name = os.environ.get("DEFAULT_ORG_NAME", "Atticus Default")
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_name = os.environ.get("ADMIN_NAME", "Atticus Admin")

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "Organization" ("id", "name")
                    VALUES (%s, %s)
                    ON CONFLICT ("id") DO UPDATE
                    SET "name" = EXCLUDED."name"
                    """,
                    (org_id, org_name),
                )
                if verbose:
                    print(f"Upserted organization {org_id}", file=sys.stderr)

                if admin_email:
                    admin_id = "user-seed-admin"
                    cur.execute(
                        """
                        INSERT INTO "User" ("id", "email", "name", "role", "orgId")
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT ("email") DO UPDATE
                        SET "name" = EXCLUDED."name",
                            "role" = EXCLUDED."role",
                            "orgId" = EXCLUDED."orgId"
                        """,
                        (admin_id, admin_email.lower(), admin_name, "ADMIN", org_id),
                    )
                    if verbose:
                        print(f"Ensured admin account {admin_email}", file=sys.stderr)

                user_ids: dict[str, str] = {}
                for user in SEED_USERS:
                    cur.execute(
                        """
                        INSERT INTO "User" ("id", "email", "name", "role", "orgId")
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT ("id") DO UPDATE
                        SET "email" = EXCLUDED."email",
                            "name" = EXCLUDED."name",
                            "role" = EXCLUDED."role",
                            "orgId" = EXCLUDED."orgId"
                        RETURNING "id"
                        """,
                        (
                            user["id"],
                            user["email"],
                            user["name"],
                            user["role"],
                            org_id,
                        ),
                    )
                    returned_id = cur.fetchone()[0]
                    user_ids[user["id"]] = returned_id
                    if verbose:
                        print(f"Seeded user {returned_id}", file=sys.stderr)

                author_id = user_ids["user-seed-author"]
                approver_id = user_ids["user-seed-approver"]

                for entry in GLOSSARY_SEEDS:
                    aliases = _dedupe_preserve(
                        [
                            str(item).strip()
                            for item in entry.get("aliases", [])
                            if str(item).strip()
                        ]
                    )
                    units = _dedupe_preserve(
                        [str(item).strip() for item in entry.get("units", []) if str(item).strip()]
                    )
                    families = _dedupe_preserve(
                        [
                            str(item).strip()
                            for item in entry.get("product_families", [])
                            if str(item).strip()
                        ]
                    )
                    alias_tokens: list[str] = []
                    for raw in [entry["term"], *entry.get("synonyms", []), *aliases]:
                        token = _normalize_token(raw)
                        if token:
                            alias_tokens.append(token)
                    normalized_aliases = _dedupe_preserve(alias_tokens)

                    family_tokens: list[str] = []
                    for raw in families:
                        normalized = _normalize_family(raw)
                        if normalized:
                            family_tokens.append(normalized)
                    normalized_families = _dedupe_preserve(family_tokens)
                    cur.execute(
                        """
                        INSERT INTO "GlossaryEntry"
                            ("id", "term", "definition", "synonyms", "aliases", "units",
                             "productFamilies", "normalizedAliases", "normalizedFamilies", "status",
                             "orgId", "authorId", "reviewerId", "reviewNotes", "reviewedAt")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ("id") DO UPDATE
                        SET "term" = EXCLUDED."term",
                            "definition" = EXCLUDED."definition",
                            "synonyms" = EXCLUDED."synonyms",
                            "aliases" = EXCLUDED."aliases",
                            "units" = EXCLUDED."units",
                            "productFamilies" = EXCLUDED."productFamilies",
                            "normalizedAliases" = EXCLUDED."normalizedAliases",
                            "normalizedFamilies" = EXCLUDED."normalizedFamilies",
                            "status" = EXCLUDED."status",
                            "orgId" = EXCLUDED."orgId",
                            "authorId" = EXCLUDED."authorId",
                            "reviewerId" = EXCLUDED."reviewerId",
                            "reviewNotes" = EXCLUDED."reviewNotes",
                            "reviewedAt" = EXCLUDED."reviewedAt"
                        """,
                        (
                            entry["id"],
                            entry["term"],
                            entry["definition"],
                            entry["synonyms"],
                            aliases,
                            units,
                            families,
                            normalized_aliases,
                            normalized_families,
                            entry["status"],
                            org_id,
                            author_id,
                            entry.get("reviewer_id"),
                            entry.get("review_notes"),
                            _parse_datetime(entry.get("reviewed_at")),
                        ),
                    )
                    if verbose:
                        print(f"Seeded glossary entry {entry['id']}", file=sys.stderr)

                for chat in CHAT_SEEDS:
                    chat_id = chat["id"]
                    chat_user = chat.get("user_id", author_id)
                    reviewed_by = chat.get("reviewed_by_id")
                    reviewed_at = _parse_datetime(chat.get("reviewed_at"))
                    follow_up = chat.get("follow_up_prompt")

                    cur.execute(
                        """
                        INSERT INTO "Chat"
                            ("id", "orgId", "userId", "question", "answer", "confidence",
                             "status", "requestId", "topSources", "auditLog", "createdAt",
                             "reviewedById", "reviewedAt", "followUpPrompt")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ("id") DO UPDATE
                        SET "question" = EXCLUDED."question",
                            "answer" = EXCLUDED."answer",
                            "confidence" = EXCLUDED."confidence",
                            "status" = EXCLUDED."status",
                            "requestId" = EXCLUDED."requestId",
                            "topSources" = EXCLUDED."topSources",
                            "auditLog" = EXCLUDED."auditLog",
                            "userId" = EXCLUDED."userId",
                            "reviewedById" = EXCLUDED."reviewedById",
                            "reviewedAt" = EXCLUDED."reviewedAt",
                            "followUpPrompt" = EXCLUDED."followUpPrompt"
                        RETURNING "id"
                        """,
                        (
                            chat_id,
                            org_id,
                            chat_user,
                            chat["question"],
                            chat.get("answer"),
                            chat["confidence"],
                            chat["status"],
                            chat.get("request_id"),
                            _json(chat.get("top_sources", [])),
                            _json(chat.get("audit_log", [])),
                            _parse_datetime(chat.get("created_at")),
                            reviewed_by,
                            reviewed_at,
                            follow_up,
                        ),
                    )
                    cur.fetchone()
                    if verbose:
                        print(f"Upserted chat {chat_id}", file=sys.stderr)

                    cur.execute(
                        """
                        INSERT INTO "RagEvent"
                            ("id", "orgId", "actorId", "actorRole", "action", "entity",
                             "chatId", "requestId", "after")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ("id") DO UPDATE
                        SET "orgId" = EXCLUDED."orgId",
                            "actorId" = EXCLUDED."actorId",
                            "actorRole" = EXCLUDED."actorRole",
                            "action" = EXCLUDED."action",
                            "entity" = EXCLUDED."entity",
                            "chatId" = EXCLUDED."chatId",
                            "requestId" = EXCLUDED."requestId",
                            "after" = EXCLUDED."after"
                        """,
                        (
                            f"{chat_id}-captured",
                            org_id,
                            chat_user,
                            "USER",
                            "chat.captured",
                            "chat",
                            chat_id,
                            chat.get("request_id"),
                            _json({"status": chat["status"], "confidence": chat["confidence"]}),
                        ),
                    )

                    if follow_up:
                        cur.execute(
                            """
                            INSERT INTO "RagEvent"
                                ("id", "orgId", "actorId", "actorRole", "action", "entity",
                                 "chatId", "requestId", "after")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT ("id") DO UPDATE
                            SET "orgId" = EXCLUDED."orgId",
                                "actorId" = EXCLUDED."actorId",
                                "actorRole" = EXCLUDED."actorRole",
                                "action" = EXCLUDED."action",
                                "entity" = EXCLUDED."entity",
                                "chatId" = EXCLUDED."chatId",
                                "requestId" = EXCLUDED."requestId",
                                "after" = EXCLUDED."after"
                            """,
                            (
                                f"{chat_id}-followup",
                                org_id,
                                approver_id,
                                "ADMIN",
                                "chat.followup_recorded",
                                "chat",
                                chat_id,
                                chat.get("request_id"),
                                _json({"followUpPrompt": follow_up}),
                            ),
                        )

                    tickets = chat.get("tickets", [])
                    for ticket in tickets:
                        cur.execute(
                            """
                            INSERT INTO "Ticket"
                                ("id", "orgId", "chatId", "key", "status", "assignee",
                                 "lastActivity", "summary", "auditLog")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT ("id") DO UPDATE
                            SET "key" = EXCLUDED."key",
                                "status" = EXCLUDED."status",
                                "assignee" = EXCLUDED."assignee",
                                "lastActivity" = EXCLUDED."lastActivity",
                                "summary" = EXCLUDED."summary",
                                "auditLog" = EXCLUDED."auditLog",
                                "chatId" = EXCLUDED."chatId",
                                "orgId" = EXCLUDED."orgId"
                            """,
                            (
                                ticket["id"],
                                org_id,
                                chat_id,
                                ticket["key"],
                                ticket["status"],
                                ticket.get("assignee"),
                                _parse_datetime(ticket.get("last_activity")),
                                ticket.get("summary"),
                                _json(ticket.get("audit_log", [])),
                            ),
                        )

                    if tickets:
                        first_ticket = tickets[0]
                        cur.execute(
                            """
                            INSERT INTO "RagEvent"
                                ("id", "orgId", "actorId", "actorRole", "action", "entity",
                                 "chatId", "requestId", "after")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT ("id") DO UPDATE
                            SET "orgId" = EXCLUDED."orgId",
                                "actorId" = EXCLUDED."actorId",
                                "actorRole" = EXCLUDED."actorRole",
                                "action" = EXCLUDED."action",
                                "entity" = EXCLUDED."entity",
                                "chatId" = EXCLUDED."chatId",
                                "requestId" = EXCLUDED."requestId",
                                "after" = EXCLUDED."after"
                            """,
                            (
                                f"{chat_id}-escalated",
                                org_id,
                                approver_id,
                                "ADMIN",
                                "chat.escalated",
                                "chat",
                                chat_id,
                                chat.get("request_id"),
                                _json({"status": "escalated", "ticket": first_ticket["key"]}),
                            ),
                        )

                if verbose:
                    print("Database seed completed", file=sys.stderr)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the Atticus database with reference data.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Echo progress information while seeding.",
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown and args.verbose:
        print(f"Ignoring extra arguments: {unknown}", file=sys.stderr)
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        seed_database(verbose=args.verbose)
    except Exception as exc:  # pragma: no cover - surfaced in tests if triggered
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
