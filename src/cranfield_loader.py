"""Parse the raw Cranfield files into stable, typed records.

Sprint 1 task: "identify document IDs, document text, query IDs, query text and
qrels" and ensure "stable IDs" with "relevance judgments linked to the correct
query and document IDs."

Two well-known Cranfield conventions are handled explicitly here:

1. Query ID mismatch.
   ``cran.qry`` contains 225 queries, but their ``.I`` labels are NOT 1..225 --
   they run 1, 2, 4, ... 365 (the original question numbers).  The relevance
   judgments in ``cranqrel``, however, use the SEQUENTIAL position of the query
   in the file (1..225).  We therefore assign ``query_id`` = file position and
   keep the printed label as ``orig_id`` for traceability.  Downstream code must
   join qrels on ``query_id``, never on ``orig_id``.

2. Document field layout.
   Each document has .I (id), .T (title), .A (author), .B (bibliography) and
   .W (abstract/body).  The ``.W`` field repeats the title text as its first
   lines -- this is part of the original collection and is preserved as-is.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

_FIELD_TAGS = {".T", ".A", ".B", ".W"}
_ID_RE = re.compile(r"^\.I\s+(\d+)")


@dataclass
class Document:
    doc_id: int          # stable 1..1400 (from the .I label, which IS sequential for docs)
    title: str
    author: str
    bib: str
    body: str            # the .W abstract (includes the repeated title)


@dataclass
class Query:
    query_id: int        # sequential 1..225 -- THIS is what qrels reference
    orig_id: int         # the original .I label (non-sequential, up to 365)
    text: str


@dataclass
class QRel:
    query_id: int        # joins to Query.query_id
    doc_id: int          # joins to Document.doc_id
    relevance: int       # raw Cranfield code: -1, 1, 2, 3, 4


@dataclass
class Cranfield:
    documents: List[Document] = field(default_factory=list)
    queries: List[Query] = field(default_factory=list)
    qrels: List[QRel] = field(default_factory=list)


def _read(path: Path) -> List[str]:
    # The collection is 1990s ASCII; latin-1 decodes every byte without error.
    return path.read_text(encoding="latin-1").splitlines()


def load_documents(path: Path) -> List[Document]:
    docs: List[Document] = []
    cur_id = None
    fields = {"T": [], "A": [], "B": [], "W": []}
    cur_tag = None

    def flush():
        if cur_id is not None:
            docs.append(
                Document(
                    doc_id=cur_id,
                    title=" ".join(fields["T"]).strip(),
                    author=" ".join(fields["A"]).strip(),
                    bib=" ".join(fields["B"]).strip(),
                    body=" ".join(fields["W"]).strip(),
                )
            )

    for line in _read(path):
        m = _ID_RE.match(line)
        if m:
            flush()
            cur_id = int(m.group(1))
            fields = {"T": [], "A": [], "B": [], "W": []}
            cur_tag = None
        elif line.strip() in _FIELD_TAGS:
            cur_tag = line.strip()[1]  # 'T' / 'A' / 'B' / 'W'
        elif cur_tag is not None:
            fields[cur_tag].append(line.strip())
    flush()
    return docs


def load_queries(path: Path) -> List[Query]:
    queries: List[Query] = []
    seq = 0
    cur_orig = None
    text_lines: List[str] = []
    in_w = False

    def flush():
        nonlocal seq
        if cur_orig is not None:
            seq += 1
            queries.append(
                Query(query_id=seq, orig_id=cur_orig, text=" ".join(text_lines).strip())
            )

    for line in _read(path):
        m = _ID_RE.match(line)
        if m:
            flush()
            cur_orig = int(m.group(1))
            text_lines = []
            in_w = False
        elif line.strip() == ".W":
            in_w = True
        elif in_w:
            text_lines.append(line.strip())
    flush()
    return queries


def load_qrels(path: Path) -> List[QRel]:
    qrels: List[QRel] = []
    for line in _read(path):
        parts = line.split()
        if len(parts) < 3:
            continue
        q, d, r = int(parts[0]), int(parts[1]), int(parts[2])
        qrels.append(QRel(query_id=q, doc_id=d, relevance=r))
    return qrels


def load_cranfield(raw_dir: Path = RAW_DIR) -> Cranfield:
    """Load all three files into a single typed container."""
    return Cranfield(
        documents=load_documents(raw_dir / "cran.all.1400"),
        queries=load_queries(raw_dir / "cran.qry"),
        qrels=load_qrels(raw_dir / "cranqrel"),
    )


if __name__ == "__main__":
    data = load_cranfield()
    print(f"documents: {len(data.documents)}")
    print(f"queries  : {len(data.queries)}")
    print(f"qrels    : {len(data.qrels)}")
    print("\nexample document:")
    d = data.documents[0]
    print(f"  doc_id={d.doc_id}  title={d.title[:60]!r}")
    print("\nexample query:")
    q = data.queries[2]
    print(f"  query_id={q.query_id}  orig_id={q.orig_id}  text={q.text[:60]!r}")
