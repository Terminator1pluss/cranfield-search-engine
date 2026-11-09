"""Text preprocessing pipeline: clean -> tokenize -> stop-word removal -> stem.

Sprint 1 task: "Implement text cleaning, tokenization, stop-word removal and
stemming" as a reproducible, documented component.

Design choices (documented so Sprint 2+ stays consistent):
  * Lowercasing + ASCII-letter tokenization via a regex.  We deliberately avoid
    NLTK's ``punkt`` sentence tokenizer -- it adds a fragile data download and
    buys nothing for bag-of-words IR.  A ``[a-z]+`` tokenizer is deterministic
    and dependency-light.
  * Stop words: NLTK's English list (198 words).
  * Stemming: Porter stemmer (the IR standard, matches most BM25/TF-IDF setups).
  * Each stage is independently toggleable so the same code serves ablations.

The function is pure and deterministic: identical input always yields identical
tokens, which the test-suite asserts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List

from nltk.stem import PorterStemmer

# Token = run of ASCII letters; digits and punctuation are dropped.  This also
# cleanly handles the collection's slashed markup like /destalling/.
_TOKEN_RE = re.compile(r"[a-z]+")


@lru_cache(maxsize=1)
def _stopwords() -> frozenset:
    """Load NLTK English stop words, downloading the corpus once if needed."""
    import nltk

    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords

    return frozenset(stopwords.words("english"))


@lru_cache(maxsize=1)
def _stemmer() -> PorterStemmer:
    return PorterStemmer()


@dataclass(frozen=True)
class PreprocessConfig:
    lowercase: bool = True
    remove_stopwords: bool = True
    stem: bool = True
    min_token_len: int = 2        # drop 1-char tokens ('a', single letters)


DEFAULT_CONFIG = PreprocessConfig()


def clean_text(text: str, lowercase: bool = True) -> str:
    """Normalise whitespace and (optionally) case."""
    text = text.replace("\n", " ")
    if lowercase:
        text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> List[str]:
    """Split cleaned text into ASCII-letter tokens."""
    return _TOKEN_RE.findall(text)


def preprocess(text: str, config: PreprocessConfig = DEFAULT_CONFIG) -> List[str]:
    """Full pipeline: clean -> tokenize -> filter -> (stopwords) -> (stem)."""
    cleaned = clean_text(text, lowercase=config.lowercase)
    tokens = tokenize(cleaned)

    if config.min_token_len > 1:
        tokens = [t for t in tokens if len(t) >= config.min_token_len]

    if config.remove_stopwords:
        stops = _stopwords()
        tokens = [t for t in tokens if t not in stops]

    if config.stem:
        stem = _stemmer().stem
        tokens = [stem(t) for t in tokens]

    return tokens


if __name__ == "__main__":
    sample = ("Experimental investigation of the aerodynamics of a wing "
              "in a slipstream .")
    print("raw    :", sample)
    print("cleaned:", clean_text(sample))
    print("tokens :", tokenize(clean_text(sample)))
    print("final  :", preprocess(sample))
