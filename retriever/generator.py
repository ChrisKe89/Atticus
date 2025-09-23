"""LLM generation helpers."""

from __future__ import annotations

import importlib
import logging
import os
import re
from collections.abc import Iterable
from typing import Any, cast

from rapidfuzz import fuzz

from atticus.config import AppSettings


class GeneratorClient:
    """Wrapper around OpenAI responses with offline fallback."""

    def __init__(self, settings: AppSettings, logger: logging.Logger | None = None) -> None:
        self.settings = settings
        self.logger = logger or logging.getLogger("atticus")
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self._client: Any | None = None
        if api_key:  # pragma: no cover - requires network
            try:
                openai_module = importlib.import_module("openai")
                openai_class = cast(Any, openai_module).OpenAI
                # Pass the key explicitly so we don't rely on process env
                self._client = openai_class(api_key=api_key)
            except Exception as exc:  # pragma: no cover - network path
                self.logger.warning(
                    "OpenAI client unavailable; using offline summarizer",
                    extra={"extra_payload": {"error": str(exc)}},
                )
        else:
            self.logger.info("No OpenAI API key detected; using offline summarizer")

    def generate(  # noqa: PLR0912, PLR0915
        self,
        prompt: str,
        contexts: Iterable[str],
        citations: Iterable[str] | None = None,
        temperature: float = 0.2,
    ) -> str:
        context_text = "\n\n".join(contexts)
        if not context_text:
            return "I was unable to find supporting context for this question."

        if self._client is not None:  # pragma: no cover - requires network
            try:
                system_prompt = "You are Atticus, a factual assistant. Respond with concise paragraphs and cite the provided context snippets."
                user_prompt = f"Context:\n{context_text}\n\nPrompt:\n{prompt}"
                response: Any = self._client.responses.create(
                    model=self.settings.generation_model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )
                if getattr(response, "output", None):
                    first_output = response.output[0]
                    content = getattr(first_output, "content", None)
                    if content and getattr(content[0], "text", None):
                        return str(content[0].text).strip()
            except Exception as exc:
                self.logger.error(
                    "OpenAI generation failed; using offline summarizer",
                    extra={"extra_payload": {"error": str(exc)}},
                )

        # Offline: try Q/A matching first, then specialized heuristics, then summary
        lowered_prompt = prompt.lower()
        # Q/A pairs like: "Q: ..." followed later by "A: ..."
        try:
            QA_MATCH_THRESHOLD = 0.6
            for block in contexts:
                lines = block.splitlines()
                content_lines = lines[1:] if lines and ":" in lines[0] else lines
                for i, line in enumerate(content_lines):
                    if line.strip().lower().startswith("q:"):
                        q_text = line.split(":", 1)[1].strip()
                        score = fuzz.partial_ratio(lowered_prompt, q_text.lower()) / 100.0
                        if score >= QA_MATCH_THRESHOLD:
                            for j in range(i + 1, min(i + 5, len(content_lines))):
                                nxt = content_lines[j].strip()
                                if nxt.lower().startswith("a:"):
                                    return nxt.split(":", 1)[1].strip()
        except Exception:
            pass

        # Lightweight heuristic for common spec-style questions when offline
        lowered_prompt = prompt.lower()
        if any(key in lowered_prompt for key in ["resolution", "dpi", "print resolution"]):
            phrases: list[str] = []
            for block in contexts:
                # Search each line for DPI patterns (e.g., 1200 x 1200 dpi, 600 dpi)
                for line in block.splitlines():
                    m_iter = re.finditer(
                        r"\b(?:up to\s*)?(?:\d{2,4}\s*[x×]\s*\d{2,4}|\d{2,4})\s*dpi\b(?:\s*[A-Za-z/ ]*)?",
                        line,
                        flags=re.IGNORECASE,
                    )
                    for m in m_iter:
                        phrase = re.sub(r"\s+", " ", m.group(0)).strip()
                        if phrase.lower() not in {p.lower() for p in phrases}:
                            phrases.append(phrase)
            if phrases:
                header = "Print resolution"
                # Prefer the richest phrase (contains x)
                phrases.sort(key=lambda p: ("x" not in p.lower(), len(p)))
                body = "; ".join(phrases[:3])
                lines = [f"{header}: {body}"]
                cite_list = list(citations or [])
                if cite_list:
                    lines.append("")
                    lines.append("Citations:")
                    for idx, citation in enumerate(cite_list[:10], start=1):
                        lines.append(f"[{idx}] {citation}")
                return "\n".join(lines)

        summary_lines = ["I found the following grounded details:"]
        for idx, snippet in enumerate(contexts, start=1):
            headline = snippet.splitlines()[0][:200]
            summary_lines.append(f"- [{idx}] {headline}")
        citation_list = list(citations or [])
        if citation_list:
            summary_lines.append("")
            summary_lines.append("Citations:")
            for idx, citation in enumerate(citation_list, start=1):
                summary_lines.append(f"[{idx}] {citation}")
        return "\n".join(summary_lines)

    def heuristic_confidence(self, answer: str) -> float:
        lowered = answer.lower()
        # If we produced a clear spec with DPI, boost confidence slightly
        if "dpi" in lowered:
            import re  # noqa: PLC0415

            if re.search(r"\b\d{2,4}\s*(?:[x×]\s*\d{2,4}\s*)?dpi\b", lowered):
                return 0.9
        if any(token in lowered for token in ["not sure", "cannot", "unable", "insufficient"]):
            return 0.3
        if "confidence" in lowered and "%" in lowered:
            try:
                percent_tokens = (
                    int(token.strip("%"))
                    for token in lowered.split()
                    if token.strip("% ").isdigit()
                )
                percent = next(percent_tokens)
                return max(0.0, min(1.0, percent / 100.0))
            except Exception:
                return 0.6
        return 0.8
