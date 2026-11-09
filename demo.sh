#!/usr/bin/env bash
#
# demo.sh — Sprint 1 live demonstration driver (Cranfield Search Engine)
#
# Runs the Sprint 1 story one step at a time, pausing between steps so you can
# talk. Press ENTER to advance. Run with --auto to play straight through, or
# --no-pause as an alias.
#
#   ./demo.sh            # interactive (recommended for the live demo)
#   ./demo.sh --auto     # no pauses
#
set -u

# --- always run from this script's own directory (the project/ folder) -------
cd "$(dirname "$0")" || exit 1

PY=python3
PAUSE=1
case "${1:-}" in --auto|--no-pause) PAUSE=0 ;; esac

# --- colours (fall back to plain text if not a terminal) ---------------------
if [ -t 1 ]; then
  C='\033[36m'; G='\033[32m'; Y='\033[33m'; B='\033[1m'; D='\033[2m'; R='\033[0m'
else
  C=''; G=''; Y=''; B=''; D=''; R=''
fi

step=0
banner() {
  step=$((step+1))
  echo
  echo -e "${C}${B}============================================================${R}"
  echo -e "${C}${B}  STEP ${step}  ·  $1${R}"
  echo -e "${C}${B}============================================================${R}"
  [ -n "${2:-}" ] && echo -e "${D}  say: \"$2\"${R}"
  echo -e "${D}  \$ $3${R}"
  echo
}
pause() {
  if [ "$PAUSE" = "1" ]; then
    echo
    echo -ne "${Y}  [ ENTER to continue${R}${D} · Ctrl-C to stop ]${R} "
    read -r _
  fi
}

clear 2>/dev/null
echo -e "${G}${B}"
echo "   CRANFIELD SEARCH ENGINE — SPRINT 1 DEMO"
echo "   Dataset Acquisition · Inspection · Preprocessing"
echo -e "${R}${D}   Press ENTER after each step. Run with --auto to skip pauses.${R}"
pause

# --- 1. Full pipeline --------------------------------------------------------
banner "Full pipeline — download, inspect, preprocess, persist" \
  "One command runs the whole data foundation and is deterministic." \
  "python3 -m src.build_pipeline"
pause
$PY -m src.build_pipeline

# --- 2. Acceptance tests -----------------------------------------------------
banner "Acceptance tests — prove it's correct, not just running" \
  "Seven tests map to the sprint's acceptance criteria — all passing." \
  "python3 -m tests.test_pipeline"
pause
$PY -m tests.test_pipeline

# --- 3. Preprocessing on a real sentence -------------------------------------
banner "Preprocessing — raw abstract in, clean stemmed tokens out" \
  "Lowercased, tokenized, stop-words removed, Porter-stemmed." \
  "python3 -m src.preprocess"
pause
$PY -m src.preprocess

# --- 4. Smoke test -----------------------------------------------------------
banner "Smoke test — the corpus is already queryable" \
  "Not the real model yet, but trivial overlap already finds relevant docs." \
  "python3 -m src.smoke_test"
pause
$PY -m src.smoke_test

# --- 5. Show the tangible outputs --------------------------------------------
banner "Outputs — cleaned corpus, qrels, vocabulary and figures" \
  "Everything is persisted and ready for Sprint 2." \
  "ls -lh data/processed  &&  open data/processed/figures"
pause
ls -lh data/processed
if command -v open >/dev/null 2>&1; then
  open data/processed/figures 2>/dev/null
fi

echo
echo -e "${G}${B}  ✓ Sprint 1 demo complete — pipeline, tests and smoke test all green.${R}"
echo -e "${D}    Next: Sprint 2 — inverted index, TF-IDF and BM25.${R}"
echo
