# Cranfield Search Engine — Project 1

A document retrieval system built on the **Cranfield** test collection using
classical and hybrid Information Retrieval techniques. This repository tracks the
4-sprint plan; the code below covers **Sprint 1 — Dataset & Preprocessing**.

> Sprint 1 scope: obtain and inspect the Cranfield dataset, implement a
> reproducible cleaning / tokenization / stop-word / stemming pipeline, and
> prepare a small query set for smoke testing. TF-IDF, BM25, dense retrieval,
> RRF, the search interface and evaluation arrive in Sprints 2–4.

## Dataset

Cranfield collection (University of Glasgow distribution):

| File            | Contents                                            |
|-----------------|-----------------------------------------------------|
| `cran.all.1400` | 1,400 aeronautical abstracts (SMART field format)   |
| `cran.qry`      | 225 queries                                         |
| `cranqrel`      | 1,837 relevance judgments (`query_id doc_id code`)  |

## Setup

```bash
cd project
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
```

NLTK's `stopwords` corpus is downloaded automatically on first run. No `punkt`
download is needed — tokenization is a dependency-light regex.

## Run

```bash
# Full pipeline: download -> load -> inspect -> preprocess -> save outputs + figures
python -m src.build_pipeline

# Acceptance tests
python -m tests.test_pipeline          # or: pytest -q

# End-to-end sanity check on a small query set
python -m src.smoke_test
```

Each module is also runnable on its own (`python -m src.cranfield_loader`,
`python -m src.preprocess`, `python -m src.download_data`).

## Outputs (`data/processed/`)

| File                     | Description                                              |
|--------------------------|----------------------------------------------------------|
| `documents.jsonl`        | one JSON per document, with `tokens` (preprocessed)      |
| `queries.jsonl`          | one JSON per query, with `query_id`, `orig_id`, `tokens` |
| `qrels.tsv`              | `query_id · doc_id · relevance`                          |
| `inspection_report.json` | completeness / duplicates / label format / integrity     |
| `vocabulary.json`        | vocabulary size + top stems + preprocessing config       |
| `smoke_queries.json`     | small hand-picked query set                              |
| `figures/*.png`          | relevance, document-length, judgments-per-query charts   |

## Project layout

```
project/
├── data/
│   ├── raw/            # cran.all.1400, cran.qry, cranqrel (auto-downloaded)
│   └── processed/      # pipeline outputs + figures
├── src/
│   ├── download_data.py    # obtain the collection (idempotent)
│   ├── cranfield_loader.py # parse to typed records with stable IDs
│   ├── preprocess.py       # clean · tokenize · stop-words · Porter stem
│   ├── inspect_dataset.py  # integrity report + figures
│   ├── build_pipeline.py   # end-to-end entry point
│   └── smoke_test.py       # token-overlap sanity search
├── tests/
│   └── test_pipeline.py    # acceptance tests
├── requirements.txt
└── README.md
```

## Preprocessing conventions (fixed for later sprints)

- **Tokenizer:** lowercase, ASCII letters only (`[a-z]+`), min length 2.
- **Stop words:** NLTK English (198 words).
- **Stemming:** Porter.
- Configurable via `PreprocessConfig` for ablations.

## Key dataset findings (Sprint 1 inspection)

- **1,400** documents (IDs 1–1400), **225** queries, **1,837** judgments
  (avg **8.16** per query; every query is judged).
- **Query-ID mismatch (handled):** `cran.qry` labels run 1, 2, 4 … **365** and are
  *not* sequential. `cranqrel` uses the sequential file position **1–225**. The
  loader assigns `query_id` = position and keeps the label as `orig_id`. Join qrels
  on `query_id`, never `orig_id`.
- **Relevance codes:** `1` (complete answer) → `4` (minimum interest), plus **225
  `-1`** entries (one per query, "relevant, degree unspecified" from the merge of
  two source files). Binary convention adopted: **relevant iff code ≥ 1**
  (trec_eval default); revisited in the evaluation sprint.
- **Two malformed documents (471, 995)** have empty title/author/body in the
  original files; **995 is referenced in qrels**. Flagged, not silently dropped.
- Referential integrity: **0** qrels point to a missing query or document.
- After preprocessing: vocabulary **4,274** stems, **128,006** document tokens,
  **~91 tokens/doc**.

## Status

- [x] CR-01 Load Cranfield documents, queries and qrels
- [x] CR-02 Preprocessing pipeline
- [ ] CR-03 … CR-11 (Sprints 2–4)
