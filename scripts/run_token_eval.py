#!/usr/bin/env python3
"""Run a batch of evaluation questions against an OpenAI model and log token usage."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
from openai import OpenAI

try:
    import tiktoken
except ImportError:  # pragma: no cover - optional dependency
    tiktoken = None


def _load_env_from_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        cleaned = value.strip().strip('"').strip("'")
        if cleaned:
            os.environ[key] = cleaned


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("ac7070_TOKEN_EVAL.xlsx"),
        help="Path to the Excel workbook containing questions (default: %(default)s)",
    )
    parser.add_argument(
        "--question-column",
        default="Question",
        help="Column name in the workbook that contains the questions",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/ac7070_token_eval.csv"),
        help="Destination CSV file for results (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI chat completion model to use (default: %(default)s)",
    )
    parser.add_argument(
        "--tokenizer-model",
        default=None,
        help="Model name to use for token estimation (defaults to --model)",
    )
    parser.add_argument(
        "--system",
        default=(
            "You are Atticus, an internal knowledge assistant. Answer clearly and cite relevant "
            "documents when possible. If you lack context, say so explicitly."
        ),
        help="System prompt applied to every question (default: concise Atticus instructions)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Seconds to sleep between requests to avoid rate limits (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the questions but skip calling the API",
    )
    parser.add_argument(
        "--atticus-endpoint",
        type=str,
        default=None,
        help="Optional Atticus /api/ask endpoint (e.g. http://localhost:3000/api/ask). When provided, "
        "the script calls Atticus instead of the OpenAI API.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Optional topK override when calling Atticus.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _normalise_question(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except AttributeError:
            pass

    tokenizer_model = args.tokenizer_model or args.model

    if not args.input.exists():
        print(f"Input workbook not found: {args.input}", file=sys.stderr)
        return 2

    df = pd.read_excel(args.input)
    if args.question_column not in df.columns:
        print(
            f"Column '{args.question_column}' not found in {args.input}. "
            f"Available columns: {', '.join(df.columns)}",
            file=sys.stderr,
        )
        return 2

    questions = []
    for index, raw in df[args.question_column].items():
        text = _normalise_question(raw)
        if text:
            questions.append((index, text))

    if not questions:
        print("No questions found in the workbook.", file=sys.stderr)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        for index, question in questions:
            print(f"[{index}] {question}")
        print(f"Dry run only. Would write results to {args.output}")
        return 0

    client: OpenAI | None = None
    if not args.atticus_endpoint:
        _load_env_from_file(Path(".env"))
        if "OPENAI_API_KEY" not in os.environ:
            print(
                "OPENAI_API_KEY is not set. Export it or add it to .env before running this script.",
                file=sys.stderr,
            )
            return 2
        client = OpenAI()

    results: list[dict[str, Any]] = []
    total_input_tokens = 0
    total_output_tokens = 0

    for position, (index, question) in enumerate(questions, start=1):
        print(f"[{position}/{len(questions)}] Asking: {question}")
        answer_content = None
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        response_id = None
        error_message = None

        if args.atticus_endpoint:
            payload: dict[str, Any] = {"question": question}
            if args.top_k is not None:
                payload["topK"] = args.top_k
            try:
                atticus_response = requests.post(
                    args.atticus_endpoint,
                    json=payload,
                    timeout=60,
                )
                atticus_response.raise_for_status()
                data = atticus_response.json()
                response_id = data.get("request_id")
                if data.get("answer"):
                    answer_content = data.get("answer")
                elif data.get("answers"):
                    answers = data.get("answers")
                    if isinstance(answers, list):
                        answer_content = "\n\n".join(
                            str(answer.get("answer", ""))
                            for answer in answers
                            if isinstance(answer, dict)
                        )
                else:
                    answer_content = None
            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)
        else:
            assert client is not None  # for type checker
            try:
                response = client.chat.completions.create(
                    model=args.model,
                    messages=[
                        {"role": "system", "content": args.system},
                        {"role": "user", "content": question},
                    ],
                )
                usage = response.usage or None
                prompt_tokens = usage.prompt_tokens if usage else None
                completion_tokens = usage.completion_tokens if usage else None
                total_tokens = usage.total_tokens if usage else None
                total_input_tokens += prompt_tokens or 0
                total_output_tokens += completion_tokens or 0
                response_id = response.id
                answer_content = response.choices[0].message.content if response.choices else None
            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)

        def _estimate(text: str | None) -> int | None:
            if text is None or not text.strip():
                return None
            if tiktoken is None:
                return None
            try:
                encoding = tiktoken.encoding_for_model(tokenizer_model)
            except Exception:  # pragma: no cover - fallback when model unknown
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))

        question_tokens = _estimate(question)
        answer_tokens = _estimate(answer_content)

        if args.atticus_endpoint:
            if prompt_tokens is None:
                prompt_tokens = question_tokens
            if completion_tokens is None:
                completion_tokens = answer_tokens
            if prompt_tokens is not None or completion_tokens is not None:
                total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)
                total_input_tokens += prompt_tokens or 0
                total_output_tokens += completion_tokens or 0

        results.append(
            {
                "row_index": index,
                "question": question,
                "answer": answer_content,
                "error": error_message,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "response_id": response_id,
                "question_tokens": question_tokens,
                "answer_tokens": answer_tokens,
            }
        )

        if args.sleep:
            time.sleep(args.sleep)

    results_df = pd.DataFrame(results)
    results_df.to_csv(args.output, index=False)
    print(f"Saved results for {len(results)} questions to {args.output}")
    print(f"Total prompt tokens: {total_input_tokens}")
    print(f"Total completion tokens: {total_output_tokens}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
