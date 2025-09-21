"""Evaluation metric unit tests."""

from __future__ import annotations

import pytest

from eval.runner import _evaluate_query

EXPECTED_PARTIAL_MRR = 0.5


@pytest.mark.eval
def test_evaluate_query_perfect_match() -> None:
    results = ["doc1", "doc2", "doc3"]
    relevant = ["doc1", "doc2"]
    ndcg, recall, mrr = _evaluate_query(results, relevant)
    assert round(ndcg, 4) == 1.0
    assert round(recall, 4) == 1.0
    assert round(mrr, 4) == 1.0


@pytest.mark.eval
def test_evaluate_query_partial_match() -> None:
    results = ["docX", "doc2", "doc3", "doc1"]
    relevant = ["doc1", "doc2"]
    ndcg, recall, mrr = _evaluate_query(results, relevant)
    assert ndcg < 1.0
    assert recall == 1.0
    assert mrr == EXPECTED_PARTIAL_MRR

