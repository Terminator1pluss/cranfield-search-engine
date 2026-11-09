"""Inspect the loaded Cranfield collection for completeness and integrity.

Sprint 1 task: "Inspect dataset completeness, encoding, duplicates and
relevance-label format."

Produces a machine-readable report (dict -> JSON) covering:
  * counts (documents, queries, qrels)
  * ID ranges and the query_id vs orig_id mismatch
  * empty / missing fields
  * duplicate IDs and duplicate document bodies
  * relevance-label distribution and the -1 anomaly
  * referential integrity: every qrel points at a real query and document
  * queries with zero relevance judgments
  * basic length statistics

It also renders three figures used in the report/presentation.
"""
from __future__ import annotations

import statistics
from collections import Counter
from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")  # headless / deterministic rendering
import matplotlib.pyplot as plt

from .cranfield_loader import Cranfield

# Cranfield relevance codes (from cranqrel.readme).  Lower number == more relevant.
RELEVANCE_MEANING = {
    -1: "relevant, degree unspecified (merge anomaly)",
    1: "complete answer to the question",
    2: "high degree of relevance",
    3: "useful (background / methods)",
    4: "minimum interest (e.g. historical)",
}

# Documented convention for later sprints: a document is RELEVANT iff label >= 1.
# This is the trec_eval default (rel > 0).  The 225 '-1' entries are therefore
# treated as NON-relevant under the binary convention but retained in the data
# so the decision can be revisited during the evaluation sprint.
BINARY_RELEVANT_MIN = 1


def inspect(data: Cranfield) -> Dict:
    docs, queries, qrels = data.documents, data.queries, data.qrels

    doc_ids = [d.doc_id for d in docs]
    query_ids = [q.query_id for q in queries]
    orig_ids = [q.orig_id for q in queries]
    doc_id_set = set(doc_ids)
    query_id_set = set(query_ids)

    # --- duplicates -------------------------------------------------------
    dup_doc_ids = [i for i, c in Counter(doc_ids).items() if c > 1]
    dup_query_ids = [i for i, c in Counter(query_ids).items() if c > 1]
    body_counts = Counter(d.body for d in docs)
    dup_bodies = sum(1 for c in body_counts.values() if c > 1)

    # --- empty / missing fields ------------------------------------------
    empty_titles = sum(1 for d in docs if not d.title)
    empty_body_ids = [d.doc_id for d in docs if not d.body]
    empty_queries = sum(1 for q in queries if not q.text)
    qrel_doc_set = {r.doc_id for r in qrels}
    empty_bodies_in_qrels = [i for i in empty_body_ids if i in qrel_doc_set]

    # --- relevance label format ------------------------------------------
    label_dist = Counter(r.relevance for r in qrels)

    # --- referential integrity ------------------------------------------
    qrel_bad_query = [r for r in qrels if r.query_id not in query_id_set]
    qrel_bad_doc = [r for r in qrels if r.doc_id not in doc_id_set]
    qrels_per_query = Counter(r.query_id for r in qrels)
    queries_without_qrels = sorted(query_id_set - set(qrels_per_query))

    # --- length statistics (raw whitespace tokens) -----------------------
    doc_lengths = [len(d.body.split()) for d in docs]
    query_lengths = [len(q.text.split()) for q in queries]

    report = {
        "counts": {
            "documents": len(docs),
            "queries": len(queries),
            "qrels": len(qrels),
        },
        "id_ranges": {
            "doc_id_min": min(doc_ids),
            "doc_id_max": max(doc_ids),
            "query_id_min": min(query_ids),
            "query_id_max": max(query_ids),
            "orig_query_label_min": min(orig_ids),
            "orig_query_label_max": max(orig_ids),
            "note": (
                "query_id is sequential 1..N (what qrels use); orig_id is the "
                "non-sequential .I label from cran.qry -- do NOT join on it."
            ),
        },
        "encoding": {
            "declared": "latin-1 (pure ASCII content; decodes without error)",
        },
        "duplicates": {
            "duplicate_doc_ids": dup_doc_ids,
            "duplicate_query_ids": dup_query_ids,
            "documents_with_duplicate_body_text": dup_bodies,
        },
        "missing_fields": {
            "empty_titles": empty_titles,
            "empty_bodies": len(empty_body_ids),
            "empty_body_doc_ids": empty_body_ids,
            "empty_body_doc_ids_referenced_in_qrels": empty_bodies_in_qrels,
            "empty_query_texts": empty_queries,
        },
        "relevance_labels": {
            "distribution": dict(sorted(label_dist.items())),
            "meaning": RELEVANCE_MEANING,
            "binary_convention": f"relevant iff label >= {BINARY_RELEVANT_MIN}",
            "minus_one_count": label_dist.get(-1, 0),
        },
        "referential_integrity": {
            "qrels_pointing_to_missing_query": len(qrel_bad_query),
            "qrels_pointing_to_missing_document": len(qrel_bad_doc),
            "queries_with_judgments": len(qrels_per_query),
            "queries_without_judgments": queries_without_qrels,
            "avg_qrels_per_query": round(len(qrels) / max(len(qrels_per_query), 1), 2),
        },
        "length_stats": {
            "doc_body_tokens_mean": round(statistics.mean(doc_lengths), 1),
            "doc_body_tokens_min": min(doc_lengths),
            "doc_body_tokens_max": max(doc_lengths),
            "query_tokens_mean": round(statistics.mean(query_lengths), 1),
            "query_tokens_min": min(query_lengths),
            "query_tokens_max": max(query_lengths),
        },
    }
    return report


def render_figures(data: Cranfield, report: Dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Relevance label distribution
    dist = report["relevance_labels"]["distribution"]
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = [str(k) for k in dist]
    ax.bar(labels, list(dist.values()), color="#4C78A8")
    ax.set_title("Cranfield relevance-label distribution")
    ax.set_xlabel("relevance code (1=best … 4=min; -1=unspecified)")
    ax.set_ylabel("number of judgments")
    for x, v in zip(labels, dist.values()):
        ax.text(x, v, str(v), ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "relevance_label_distribution.png", dpi=120)
    plt.close(fig)

    # 2. Document body length distribution
    doc_lengths = [len(d.body.split()) for d in data.documents]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(doc_lengths, bins=30, color="#72B7B2")
    ax.set_title("Document length distribution (abstract word count)")
    ax.set_xlabel("words per document body")
    ax.set_ylabel("number of documents")
    fig.tight_layout()
    fig.savefig(out_dir / "document_length_distribution.png", dpi=120)
    plt.close(fig)

    # 3. Judgments-per-query distribution
    from collections import Counter as _C

    per_query = _C(r.query_id for r in data.qrels)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(list(per_query.values()), bins=20, color="#E45756")
    ax.set_title("Relevance judgments per query")
    ax.set_xlabel("number of judged documents")
    ax.set_ylabel("number of queries")
    fig.tight_layout()
    fig.savefig(out_dir / "qrels_per_query_distribution.png", dpi=120)
    plt.close(fig)


def format_report(report: Dict) -> str:
    """Human-readable console summary."""
    c = report["counts"]
    ri = report["referential_integrity"]
    dup = report["duplicates"]
    lab = report["relevance_labels"]
    lines = [
        "=" * 60,
        "CRANFIELD DATASET INSPECTION",
        "=" * 60,
        f"documents                 : {c['documents']}",
        f"queries                   : {c['queries']}",
        f"relevance judgments       : {c['qrels']}",
        "-" * 60,
        f"doc id range              : {report['id_ranges']['doc_id_min']}"
        f"..{report['id_ranges']['doc_id_max']}",
        f"query id range (seq)      : {report['id_ranges']['query_id_min']}"
        f"..{report['id_ranges']['query_id_max']}",
        f"orig query label range    : {report['id_ranges']['orig_query_label_min']}"
        f"..{report['id_ranges']['orig_query_label_max']}  (non-sequential!)",
        "-" * 60,
        f"duplicate doc ids         : {len(dup['duplicate_doc_ids'])}",
        f"duplicate query ids       : {len(dup['duplicate_query_ids'])}",
        f"dup document body texts   : {dup['documents_with_duplicate_body_text']}",
        f"empty bodies              : {report['missing_fields']['empty_bodies']}",
        "-" * 60,
        f"relevance distribution    : {lab['distribution']}",
        f"'-1' anomaly count        : {lab['minus_one_count']}",
        f"binary convention         : {lab['binary_convention']}",
        "-" * 60,
        f"qrels -> missing query    : {ri['qrels_pointing_to_missing_query']}",
        f"qrels -> missing document : {ri['qrels_pointing_to_missing_document']}",
        f"queries with judgments    : {ri['queries_with_judgments']}",
        f"queries without judgments : {ri['queries_without_judgments']}",
        f"avg judgments / query     : {ri['avg_qrels_per_query']}",
        "=" * 60,
    ]
    return "\n".join(lines)
