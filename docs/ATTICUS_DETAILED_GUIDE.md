# Atticus Detailed Guide

## Model Name Disambiguation

1. **Direct questions** — detect precise model mentions (for example, "Apeos C4570"), scope retrieval to the matching family, and return a single answer with citations limited to that family.
2. **Unclear questions** — when parser confidence drops below the clarification threshold, respond with a `clarification` payload listing the available families and delay retrieval until the UI resubmits the original question with selected `models`.
3. **Multi-model questions** — if several models are present ("C4570 and C6580"), fan out retrieval per model and return `answers[]`, ensuring each answer carries its own `sources` while preserving the aggregated `sources` array for consumers that expect it.
4. **Follow-up flow** — UI buttons post the original prompt with `models` populated from the selected family so downstream logging and escalations have explicit model scope.

See `tests/test_model_parser.py`, `tests/test_retrieval_filters.py`, `tests/test_chat_route.py`, `tests/test_ui_route.py`, and `tests/playwright/chat.spec.ts` for executable examples.
