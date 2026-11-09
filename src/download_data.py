"""Download and extract the Cranfield test collection.

Sprint 1 task: "Obtain the Cranfield dataset."

The canonical classic-format files are distributed by the University of Glasgow
IR group as a single tarball.  We download it into ``data/raw/`` and extract the
three files the rest of the pipeline consumes:

    cran.all.1400   -> 1,400 documents   (SMART/Cranfield field format)
    cran.qry        -> 225 queries       (SMART/Cranfield field format)
    cranqrel        -> relevance judgments (query_id  doc_id  relevance)

The download is idempotent: if the files already exist it does nothing unless
``force=True`` is passed.
"""
from __future__ import annotations

import tarfile
import urllib.request
from pathlib import Path

# Primary source (Glasgow) and a GitHub mirror as fallback.
PRIMARY_URL = "http://ir.dcs.gla.ac.uk/resources/test_collections/cran/cran.tar.gz"

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
REQUIRED_FILES = ("cran.all.1400", "cran.qry", "cranqrel")


def _already_present(raw_dir: Path) -> bool:
    return all((raw_dir / name).exists() for name in REQUIRED_FILES)


def download_cranfield(raw_dir: Path = RAW_DIR, force: bool = False) -> Path:
    """Ensure the raw Cranfield files exist in ``raw_dir`` and return the path."""
    raw_dir.mkdir(parents=True, exist_ok=True)

    if _already_present(raw_dir) and not force:
        print(f"[download] Cranfield files already present in {raw_dir}")
        return raw_dir

    tar_path = raw_dir / "cran.tar.gz"
    print(f"[download] Fetching {PRIMARY_URL}")
    urllib.request.urlretrieve(PRIMARY_URL, tar_path)  # noqa: S310 (trusted URL)

    print(f"[download] Extracting {tar_path.name}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(raw_dir)  # noqa: S202 (trusted archive)

    missing = [n for n in REQUIRED_FILES if not (raw_dir / n).exists()]
    if missing:
        raise FileNotFoundError(f"Download succeeded but files are missing: {missing}")

    print(f"[download] Ready: {', '.join(REQUIRED_FILES)} in {raw_dir}")
    return raw_dir


if __name__ == "__main__":
    download_cranfield()
