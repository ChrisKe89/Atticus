"""LLM generation helpers."""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import Iterable
from typing import Any, cast

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
                self._client = openai_class()
            except Exception as exc:  # pragma: no cover - network path
                self.logger.warning("OpenAI client unavailable; using offline summarizer", extra={"extra_payload": {"error": str(exc)}})
        else:
            self.logger.info("No OpenAI API key detected; using offline summarizer")

    def generate(
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
                system_prompt = (
                    "You are Atticus, a factual assistant. Respond with concise paragraphs and cite the provided context snippets."
                )
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
        if any(token in lowered for token in ["not sure", "cannot", "unable", "insufficient"]):
            return 0.3
        if "confidence" in lowered and "%" in lowered:
            try:
                percent_tokens = (
                    int(token.strip("%")) for token in lowered.split() if token.strip("% ").isdigit()
                )
                percent = next(percent_tokens)
                return max(0.0, min(1.0, percent / 100.0))
            except Exception:
                return 0.6
        return 0.8

