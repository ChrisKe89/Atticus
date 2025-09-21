"""CLI to export the FastAPI OpenAPI schema to disk."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate API documentation artifacts")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "api" / "openapi.json",
        help="Path to write the OpenAPI document (defaults to docs/api/openapi.json)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "yaml"),
        default="json",
        help="Output format for the schema",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation for JSON output",
    )
    return parser


def export_schema(output_path: Path, output_format: str, indent: int = 2) -> None:
    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        payload = json.dumps(schema, indent=indent, sort_keys=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        payload = yaml.safe_dump(schema, sort_keys=False)
        output_path.write_text(payload, encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    export_schema(output_path=args.output, output_format=args.format, indent=args.indent)


if __name__ == "__main__":
    main()
