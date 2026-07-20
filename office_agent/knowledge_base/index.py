"""BM25 lexical search over document chunks.

Pure stdlib, no vector DB or API key required — works offline out of the
box for the small internal HELLFIRE/TETA+PI corpus. This is deliberately
lexical, not semantic: rag-01 (session 07) owns the embeddings-based
pipeline. Swap the backend behind Chunk/BM25Index once rag-01 ships an
embedding index worth depending on; keep the ingest -> chunks -> search
interface stable so that swap doesn't ripple into email_triage/docgen.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

from office_agent.knowledge_base.ingest import RawChunk

TOKEN_RE = re.compile(r"[a-zA-Z0-9а-яА-ЯіІїЇєЄ]+")

K1 = 1.5
B = 0.75


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


@dataclass
class Chunk:
    id: int
    source: str
    heading: str
    text: str
    tokens: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, id: int, raw: RawChunk) -> "Chunk":
        return cls(id=id, source=raw.source, heading=raw.heading, text=raw.text, tokens=tokenize(raw.text))


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


class BM25Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.doc_freq: Counter[str] = Counter()
        self.term_freqs: list[Counter[str]] = []
        self.doc_lens: list[int] = []

        for chunk in chunks:
            tf = Counter(chunk.tokens)
            self.term_freqs.append(tf)
            self.doc_lens.append(len(chunk.tokens))
            for term in tf:
                self.doc_freq[term] += 1

        self.n_docs = len(chunks)
        self.avg_doc_len = (sum(self.doc_lens) / self.n_docs) if self.n_docs else 0.0

    @classmethod
    def from_raw_chunks(cls, raw_chunks: list[RawChunk]) -> "BM25Index":
        chunks = [Chunk.from_raw(i, raw) for i, raw in enumerate(raw_chunks)]
        return cls(chunks)

    def _idf(self, term: str) -> float:
        df = self.doc_freq.get(term, 0)
        return math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if self.n_docs == 0:
            return []

        query_terms = tokenize(query)
        if not query_terms:
            return []

        scores = [0.0] * self.n_docs
        for term in query_terms:
            idf = self._idf(term)
            if idf <= 0:
                continue
            for i, tf in enumerate(self.term_freqs):
                freq = tf.get(term, 0)
                if freq == 0:
                    continue
                doc_len = self.doc_lens[i]
                denom = freq + K1 * (1 - B + B * doc_len / (self.avg_doc_len or 1))
                scores[i] += idf * (freq * (K1 + 1)) / denom

        ranked = sorted(
            ((score, i) for i, score in enumerate(scores) if score > 0),
            key=lambda pair: pair[0],
            reverse=True,
        )
        return [SearchResult(chunk=self.chunks[i], score=score) for score, i in ranked[:top_k]]
