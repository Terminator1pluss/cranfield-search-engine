# Sprint 1 Demo Cheat-Sheet — Cranfield Search Engine

**Goal of Sprint 1:** build the clean, verified *data foundation* (load · inspect · preprocess) for a search engine that will compare TF-IDF, BM25, dense and hybrid (RRF) retrieval in Sprints 2–4.

---

## Pre-flight (do quietly before you start)
- [ ] Terminal open in the project folder:
      `cd ~/Downloads/project/project`
- [ ] Terminal font large (⌘ + a few times)
- [ ] Presentation opens in **Chrome**, **F** = fullscreen (test on the room's machine)
- [ ] **Do not** delete `data/raw/` or clear NLTK data (lets the pipeline run offline)
- [ ] Optional: just run `./demo.sh` and press ENTER between steps

---

## The 6-step arc (~6–8 min)

| # | Command | One line to say while it runs |
|---|---------|-------------------------------|
| 1 | *(slides 1–4)* | "Project = Cranfield search engine comparing 4 retrieval methods. Sprint 1 is the data layer so later models sit on solid ground." |
| 2 | `python3 -m src.build_pipeline` | "One command: download → inspect → preprocess → save. Deterministic — re-running gives identical output." |
| 3 | `python3 -m tests.test_pipeline` | "Seven acceptance tests — stable IDs, qrel linkage, deterministic preprocessing — all passing." |
| 4 | `python3 -m src.preprocess` | "Raw abstract in, clean stemmed tokens out: lowercase, tokenize, drop stop-words, Porter-stem." |
| 5 | `python3 -m src.smoke_test` | "Sanity check, not the real model — yet trivial word-overlap already finds relevant docs in the top 10." |
| 6 | `open data/processed/figures` | "All persisted — corpus, qrels, vocabulary, figures. Ready for Sprint 2." |

**Point at these lines in the Step-2 output:**
- `orig query label range 1..365 (non-sequential!)` → the **query-ID trap** (file labels ≠ judgment IDs; we join on the right one)
- `-1: 225` → the **−1 anomaly** (kept raw, documented: relevant iff ≥ 1)
- `empty bodies: 2` → **docs 471 & 995** flagged, not silently dropped
- `qrels -> missing query/document: 0` → **referential integrity**

---

## Key numbers (memorize these)
- **1,400** documents · **225** queries · **1,837** judgments · avg **8.16**/query
- Vocabulary after preprocessing: **4,274** stems · ~**91** tokens/doc
- **7/7** acceptance tests pass · **0** dangling references

---

## Likely questions → answers
- **Why no TF-IDF/BM25 yet?** → "That's Sprint 2. Sprint 1 is deliberately the data layer — models shouldn't debug dirty data."
- **What's the `-1` code?** → "Relevant, degree-unspecified, from merging two historical judgment files. Kept raw; binary rule (≥ 1) documented for the eval sprint."
- **Why a regex tokenizer, not NLTK's?** → "Avoids a fragile `punkt` download; deterministic and dependency-light. Still use NLTK for stop-words + Porter stemmer."
- **Is it reproducible?** → "Yes — one idempotent command, byte-identical outputs. README has the steps; it just ran from a clean state."
- **Did you invent any numbers?** → "No — every figure in the report and slides comes from this pipeline. The brief requires that." *(strong closer)*

---

## If something breaks
- Pipeline errors on download → files are already in `data/raw/`; re-run, it skips the download.
- `ModuleNotFoundError` → `pip3 install -r requirements.txt`
- Run from the **`project/`** folder, or the `python3 -m src...` imports fail.

**Backup:** if the terminal misbehaves, the figures and `inspection_report.json` in `data/processed/` already show the real results — open those and talk through them.
