"""Sprint 1 acceptance tests.

Runs with pytest (``pytest -q``) or standalone (``python -m tests.test_pipeline``).
Verifies the three acceptance criteria:
  * Documents and queries load with stable IDs.
  * Relevance judgments stay linked to correct query and document IDs.
  * Preprocessing runs consistently (deterministic) and does what it claims.
"""
from __future__ import annotations

from src.cranfield_loader import load_cranfield
from src.preprocess import PreprocessConfig, preprocess

DATA = load_cranfield()


def test_counts():
    assert len(DATA.documents) == 1400
    assert len(DATA.queries) == 225
    assert len(DATA.qrels) > 1000


def test_stable_sequential_ids():
    # Document ids are exactly 1..1400.
    assert [d.doc_id for d in DATA.documents] == list(range(1, 1401))
    # Query ids are sequential 1..225 regardless of the original .I labels.
    assert [q.query_id for q in DATA.queries] == list(range(1, 226))
    # The orig labels are NOT sequential (this is the Cranfield trap).
    assert max(q.orig_id for q in DATA.queries) > 225


def test_qrel_referential_integrity():
    doc_ids = {d.doc_id for d in DATA.documents}
    query_ids = {q.query_id for q in DATA.queries}
    for r in DATA.qrels:
        assert r.query_id in query_ids, f"qrel query {r.query_id} not found"
        assert r.doc_id in doc_ids, f"qrel doc {r.doc_id} not found"


def test_known_empty_documents():
    # The original collection ships two malformed, empty records (471, 995).
    # We assert the KNOWN state rather than zero, so a regression (e.g. the
    # parser silently dropping more bodies) is caught.
    empty = [d.doc_id for d in DATA.documents if not d.body]
    assert empty == [471, 995]


def test_preprocess_is_deterministic():
    text = "Experimental investigation of the aerodynamics of a wing."
    assert preprocess(text) == preprocess(text)


def test_preprocess_removes_stopwords_and_stems():
    tokens = preprocess("the aerodynamics of the wings")
    assert "the" not in tokens and "of" not in tokens      # stop words gone
    assert "aerodynam" in tokens                            # stemmed
    assert "wing" in tokens                                 # 'wings' -> 'wing'


def test_preprocess_toggles():
    cfg = PreprocessConfig(remove_stopwords=False, stem=False)
    tokens = preprocess("the aerodynamics", cfg)
    assert tokens == ["the", "aerodynamics"]


def _run_standalone():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS  {name}")
            passed += 1
    print(f"\n{passed} tests passed.")


if __name__ == "__main__":
    _run_standalone()
