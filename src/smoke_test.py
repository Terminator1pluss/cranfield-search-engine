"""Smoke test: prove the cleaned corpus is queryable end-to-end.

Sprint 1 acceptance: "Prepare a small set of queries for smoke testing."

This is NOT a retrieval model (TF-IDF/BM25 arrive in Sprint 2).  It runs a trivial
token-overlap score between a preprocessed query and each preprocessed document,
purely to confirm that:
  * the processed corpus loads,
  * query and document tokens share a vocabulary (preprocessing is consistent),
  * known-relevant documents (from qrels) actually surface near the top.

Run from the ``project`` directory:  python -m src.smoke_test
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

PROC_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


def _load_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def _load_qrels(path: Path):
    rel = {}
    with path.open(encoding="utf-8") as fh:
        next(fh)  # header
        for line in fh:
            q, d, r = line.split("\t")
            rel.setdefault(int(q), {})[int(d)] = int(r)
    return rel


def overlap_score(query_tokens, doc_counts: Counter) -> int:
    return sum(doc_counts.get(t, 0) for t in set(query_tokens))


def main() -> None:
    docs = _load_jsonl(PROC_DIR / "documents.jsonl")
    smoke = json.loads((PROC_DIR / "smoke_queries.json").read_text())
    qrels = _load_qrels(PROC_DIR / "qrels.tsv")

    doc_counts = {d["doc_id"]: Counter(d["tokens"]) for d in docs}

    print("Token-overlap smoke search (sanity only, not a Sprint-2 model)\n")
    for q in smoke:
        scores = (
            (doc_id, overlap_score(q["tokens"], counts))
            for doc_id, counts in doc_counts.items()
        )
        top = sorted(scores, key=lambda x: x[1], reverse=True)[:10]
        top_ids = [d for d, _ in top]
        relevant = set(qrels.get(q["query_id"], {}))
        hits = [d for d in top_ids if d in relevant]

        print(f"query_id={q['query_id']:>3} (orig {q['orig_id']}): "
              f"\"{q['text'][:55]}...\"")
        print(f"   top-10 docs : {top_ids}")
        print(f"   relevant@10 : {len(hits)}/{min(10, len(relevant))} "
              f"-> {hits}\n")


if __name__ == "__main__":
    main()
