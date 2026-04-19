"""Tests for the generation module - context building logic (no API calls)."""

from app.generation import build_context_block


def test_build_context_block_formats_correctly():
    chunks = [
        {"chunk_text": "Apple revenue was $94.9B", "source": "Apple.pdf", "pages": "1"},
    ]
    result = build_context_block(chunks)
    assert "[1]" in result
    assert "Apple.pdf" in result
    assert "p.1" in result
    assert "Apple revenue was $94.9B" in result


def test_build_context_block_multiple_chunks():
    chunks = [
        {"chunk_text": "First chunk", "source": "doc1.pdf", "pages": "1"},
        {"chunk_text": "Second chunk", "source": "doc2.pdf", "pages": "5"},
    ]
    result = build_context_block(chunks)
    assert "[1]" in result
    assert "[2]" in result
    assert "doc1.pdf" in result
    assert "doc2.pdf" in result


def test_build_context_block_missing_pages():
    chunks = [
        {"chunk_text": "Some text", "source": "doc.pdf"},
    ]
    result = build_context_block(chunks)
    assert "[1]" in result
    assert "doc.pdf" in result
    # Should not crash when pages is missing


def test_build_context_block_empty_pages():
    chunks = [
        {"chunk_text": "Some text", "source": "doc.pdf", "pages": ""},
    ]
    result = build_context_block(chunks)
    assert "p." not in result  # no page label when empty
