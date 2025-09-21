"""Tokenization utilities for chunking."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Sequence

import tiktoken


@lru_cache(maxsize=1)
def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")


def encode(text: str) -> list[int]:
    return _encoding().encode(text, disallowed_special=())


def decode(tokens: Sequence[int]) -> str:
    return _encoding().decode(list(tokens))


def count_tokens(text: str) -> int:
    return len(encode(text))


def split_tokens(tokens: Sequence[int], window: int, overlap: int) -> Iterable[tuple[int, int]]:
    if window <= 0:
        raise ValueError("window must be positive")
    if overlap >= window:
        raise ValueError("overlap must be smaller than window")

    step = max(1, window - overlap)
    total = len(tokens)
    for start in range(0, total, step):
        end = min(start + window, total)
        yield start, end
        if end == total:
            break

