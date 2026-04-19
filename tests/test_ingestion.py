"""Tests for the ingestion module - chunking and text processing logic."""

import os

from app.ingestion import chunk_pages, clean_text, ingest_document

# -- clean_text --

def test_clean_text_removes_extra_whitespace():
    assert clean_text("hello   world") == "hello world"


def test_clean_text_removes_newlines():
    assert clean_text("hello\n\nworld") == "hello world"


def test_clean_text_strips_edges():
    assert clean_text("  hello  ") == "hello"


# -- chunk_pages --

def test_chunk_pages_returns_chunks():
    pages = [{"page": 1, "text": "A" * 1000}]
    chunks = chunk_pages(pages, chunk_size=512, overlap=64)
    assert len(chunks) >= 2


def test_chunk_pages_tracks_page_numbers():
    pages = [
        {"page": 1, "text": "First page content. " * 50},
        {"page": 2, "text": "Second page content. " * 50},
    ]
    chunks = chunk_pages(pages, chunk_size=512, overlap=64)
    # First chunk should reference page 1
    assert 1 in chunks[0]["pages"]
    # Last chunk should reference page 2
    assert 2 in chunks[-1]["pages"]


def test_chunk_pages_overlap():
    """Chunks should overlap - total text covered > sum of non-overlapping chunks."""
    pages = [{"page": 1, "text": "word " * 200}]
    chunks_with_overlap = chunk_pages(pages, chunk_size=100, overlap=20)
    chunks_no_overlap = chunk_pages(pages, chunk_size=100, overlap=0)
    assert len(chunks_with_overlap) > len(chunks_no_overlap)


def test_chunk_pages_empty_page_skipped():
    pages = [
        {"page": 1, "text": "Real content here."},
        {"page": 2, "text": "   "},  # empty after cleaning
    ]
    chunks = chunk_pages(pages, chunk_size=512, overlap=64)
    assert len(chunks) >= 1
    assert all(2 not in c["pages"] for c in chunks)


# -- ingest_document --

def test_ingest_document_creates_records():
    pdf_path = os.path.join("docs", "Apple_Q24.pdf")
    if not os.path.exists(pdf_path):
        return  # skip if docs not available
    records = ingest_document(pdf_path)
    assert len(records) > 0
    assert all("id" in r for r in records)
    assert all("chunk_text" in r for r in records)
    assert all("source" in r for r in records)
    assert all("pages" in r for r in records)


def test_ingest_document_record_ids_are_unique():
    pdf_path = os.path.join("docs", "Apple_Q24.pdf")
    if not os.path.exists(pdf_path):
        return
    records = ingest_document(pdf_path)
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))
