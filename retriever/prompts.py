"""Prompt template registry for generation clients."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Represents a versioned prompt template."""

    version: str
    system: str
    user: str

    def render_system(self) -> str:
        """Return the system prompt string."""

        return self.system

    def render_user(self, *, prompt: str, context: str) -> str:
        """Format the user prompt with the provided context."""

        return self.user.format(prompt=prompt, context=context)


_PROMPT_REGISTRY: dict[str, PromptTemplate] = {
    "atticus-v1": PromptTemplate(
        version="atticus-v1",
        system=(
            "You are Atticus, a factual assistant for FUJIFILM Business Innovation. "
            "Respond with concise, grounded paragraphs, cite provided context snippets, "
            "and never fabricate sources."
        ),
        user="Context:\n{context}\n\nPrompt:\n{prompt}",
    )
}


def get_prompt_template(version: str) -> PromptTemplate:
    """Retrieve a prompt template by version or raise a KeyError."""

    if version not in _PROMPT_REGISTRY:
        raise KeyError(f"Unknown prompt template version: {version}")
    return _PROMPT_REGISTRY[version]


def available_versions() -> tuple[str, ...]:
    """Return the known prompt template versions."""

    return tuple(sorted(_PROMPT_REGISTRY))
