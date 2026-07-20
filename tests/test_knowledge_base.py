from office_agent.knowledge_base.ingest import chunk_document, ingest_directory
from office_agent.knowledge_base.index import BM25Index

SAMPLE_DOCS_DIR = "samples/docs"


def test_chunk_document_splits_by_heading():
    text = "# Title\n\nintro para\n\n## Section A\n\nfirst\n\n## Section B\n\nsecond"
    chunks = chunk_document("doc.md", text)
    headings = [c.heading for c in chunks]
    assert "Section A" in headings
    assert "Section B" in headings


def test_ingest_directory_finds_sample_docs():
    raw_chunks = ingest_directory(SAMPLE_DOCS_DIR)
    assert len(raw_chunks) > 0
    assert any("business-model.md" in c.source for c in raw_chunks)


def test_search_ranks_relevant_chunk_first():
    raw_chunks = ingest_directory(SAMPLE_DOCS_DIR)
    index = BM25Index.from_raw_chunks(raw_chunks)

    results = index.search("EU data residency DSGVO hard requirement")
    assert results
    assert "business-model.md" in results[0].chunk.source


def test_search_empty_query_returns_empty():
    index = BM25Index.from_raw_chunks(ingest_directory(SAMPLE_DOCS_DIR))
    assert index.search("") == []


def test_search_no_index_returns_empty():
    index = BM25Index.from_raw_chunks([])
    assert index.search("anything") == []
