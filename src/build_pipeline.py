"""End-to-end Sprint 1 pipeline: download -> load -> inspect -> preprocess -> save.

This is the single reproducible entry point. Run from the ``project`` directory:

    python -m src.build_pipeline

Outputs (written to data/processed/):
    documents.jsonl        one JSON object per document, incl. preprocessed tokens
    queries.jsonl          one JSON object per query, incl. preprocessed tokens
    qrels.tsv              query_id <tab> doc_id <tab> relevance
    inspection_report.json machine-readable dataset inspection
    vocabulary.json        corpus vocabulary size + most frequent stems
    smoke_queries.json     small hand-picked query set for sanity checks
    figures/*.png          dataset visualisations

Everything is deterministic: rerunning produces byte-identical outputs.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .cranfield_loader import load_cranfield
from .download_data import download_cranfield
from .inspect_dataset import format_report, inspect, render_figures
from .preprocess import DEFAULT_CONFIG, preprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROC_DIR = PROJECT_ROOT / "data" / "processed"
FIG_DIR = PROC_DIR / "figures"

# Small hand-picked query set for smoke testing (sequential query_ids).
SMOKE_QUERY_IDS = [1, 2, 3, 50, 100, 225]


def _write_jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run() -> None:
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Obtain the dataset -------------------------------------------------
    download_cranfield(RAW_DIR)

    # 2. Load into typed records -------------------------------------------
    print("[pipeline] loading raw files ...")
    data = load_cranfield(RAW_DIR)

    # 3. Inspect ------------------------------------------------------------
    print("[pipeline] inspecting dataset ...")
    report = inspect(data)
    (PROC_DIR / "inspection_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    render_figures(data, report, FIG_DIR)
    print(format_report(report))

    # 4. Preprocess + persist corpus ---------------------------------------
    print("\n[pipeline] preprocessing documents ...")
    doc_rows = []
    vocab = Counter()
    for d in data.documents:
        tokens = preprocess(d.body, DEFAULT_CONFIG)
        vocab.update(tokens)
        doc_rows.append(
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "author": d.author,
                "bib": d.bib,
                "body": d.body,
                "tokens": tokens,
                "num_tokens": len(tokens),
            }
        )
    _write_jsonl(PROC_DIR / "documents.jsonl", doc_rows)

    print("[pipeline] preprocessing queries ...")
    query_rows = []
    for q in data.queries:
        tokens = preprocess(q.text, DEFAULT_CONFIG)
        query_rows.append(
            {
                "query_id": q.query_id,
                "orig_id": q.orig_id,
                "text": q.text,
                "tokens": tokens,
                "num_tokens": len(tokens),
            }
        )
    _write_jsonl(PROC_DIR / "queries.jsonl", query_rows)

    # qrels as a clean TSV
    with (PROC_DIR / "qrels.tsv").open("w", encoding="utf-8") as fh:
        fh.write("query_id\tdoc_id\trelevance\n")
        for r in data.qrels:
            fh.write(f"{r.query_id}\t{r.doc_id}\t{r.relevance}\n")

    # 5. Vocabulary stats ---------------------------------------------------
    vocab_info = {
        "config": {
            "lowercase": DEFAULT_CONFIG.lowercase,
            "remove_stopwords": DEFAULT_CONFIG.remove_stopwords,
            "stem": DEFAULT_CONFIG.stem,
            "min_token_len": DEFAULT_CONFIG.min_token_len,
        },
        "vocabulary_size": len(vocab),
        "total_tokens": sum(vocab.values()),
        "avg_tokens_per_doc": round(sum(vocab.values()) / len(doc_rows), 1),
        "top_50_stems": vocab.most_common(50),
    }
    (PROC_DIR / "vocabulary.json").write_text(
        json.dumps(vocab_info, indent=2), encoding="utf-8"
    )

    # 6. Smoke-test query set ----------------------------------------------
    smoke = [r for r in query_rows if r["query_id"] in SMOKE_QUERY_IDS]
    (PROC_DIR / "smoke_queries.json").write_text(
        json.dumps(smoke, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"\n[pipeline] DONE. Wrote processed corpus to {PROC_DIR}\n"
        f"  vocabulary size      : {vocab_info['vocabulary_size']}\n"
        f"  total tokens (docs)  : {vocab_info['total_tokens']}\n"
        f"  avg tokens / doc     : {vocab_info['avg_tokens_per_doc']}\n"
        f"  figures              : {FIG_DIR}"
    )


if __name__ == "__main__":
    run()
