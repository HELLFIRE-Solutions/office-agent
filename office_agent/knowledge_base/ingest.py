"""Turn a directory of Markdown/text docs into search-ready chunks.

Chunking strategy: split on Markdown headings first (so a chunk stays under
one topic), then fall back to paragraph splitting for headingless blocks
longer than MAX_CHUNK_CHARS. Deliberately simple — swap this module for
rag-01's chunker once that pipeline stabilizes rather than growing this one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MAX_CHUNK_CHARS = 1500
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
DOC_EXTENSIONS = {".md", ".markdown", ".txt"}


@dataclass
class RawChunk:
    source: str
    heading: str
    text: str


def _split_by_heading(text: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("", text)]

    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        sections.append(("", text[: matches[0].start()]))

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((heading, text[start:end]))

    return sections


def _split_paragraphs(text: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    blocks: list[str] = []
    current = ""
    for p in paragraphs:
        candidate = f"{current}\n\n{p}" if current else p
        if len(candidate) > max_chars and current:
            blocks.append(current)
            current = p
        else:
            current = candidate
    if current:
        blocks.append(current)
    return blocks


def chunk_document(source: str, text: str) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    for heading, body in _split_by_heading(text):
        body = body.strip()
        if not body:
            continue
        for block in _split_paragraphs(body, MAX_CHUNK_CHARS):
            chunks.append(RawChunk(source=source, heading=heading, text=block))
    return chunks


def ingest_directory(root: str | Path) -> list[RawChunk]:
    root = Path(root)
    chunks: list[RawChunk] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in DOC_EXTENSIONS:
            text = path.read_text(encoding="utf-8", errors="ignore")
            rel = str(path.relative_to(root))
            chunks.extend(chunk_document(rel, text))
    return chunks
