# Phase 2 - Testing

## What was added

Unit tests using pytest that validate core logic WITHOUT needing API keys or external services.

## Why test in CI/CD?

Tests are the gate that prevents broken code from reaching production. If tests fail, the pipeline stops and nothing gets deployed. This catches bugs early when they are cheap to fix, not in production when they cost money and reputation.

## Files Added

### 1. `tests/__init__.py`

Empty file that marks `tests/` as a Python package. Required for pytest to discover the test files.

### 2. `tests/test_ingestion.py` (8 tests)

Tests the chunking and text processing logic. These are pure functions that don't call any external API.

| Test | What it verifies |
|------|-----------------|
| `test_clean_text_removes_extra_whitespace` | "hello   world" becomes "hello world" |
| `test_clean_text_removes_newlines` | Newlines are replaced with spaces |
| `test_clean_text_strips_edges` | Leading/trailing whitespace removed |
| `test_chunk_pages_returns_chunks` | 1000 chars of text produces multiple chunks |
| `test_chunk_pages_tracks_page_numbers` | Each chunk knows which PDF page it came from |
| `test_chunk_pages_overlap` | Overlapping chunks produce more chunks than non-overlapping |
| `test_chunk_pages_empty_page_skipped` | Blank pages don't create chunks |
| `test_ingest_document_creates_records` | Full ingestion produces records with id, text, source, pages |
| `test_ingest_document_record_ids_are_unique` | No duplicate chunk IDs |

### 3. `tests/test_generation.py` (4 tests)

Tests the context block builder that formats chunks into the prompt. Does NOT call OpenAI.

| Test | What it verifies |
|------|-----------------|
| `test_build_context_block_formats_correctly` | Output has [1], source name, page number, and chunk text |
| `test_build_context_block_multiple_chunks` | Multiple chunks get numbered [1], [2], etc. |
| `test_build_context_block_missing_pages` | No crash when pages key is missing from chunk |
| `test_build_context_block_empty_pages` | No "p." label when pages is empty string |

### 4. `tests/test_api.py` (4 tests)

Tests FastAPI endpoints using TestClient (no server needed, no API keys needed).

| Test | What it verifies |
|------|-----------------|
| `test_health_returns_200` | GET /health returns status code 200 |
| `test_health_returns_ok` | GET /health returns {"status": "ok"} |
| `test_chat_requires_question` | POST /chat with empty body returns 422 validation error |
| `test_search_requires_query` | POST /search with empty body returns 422 validation error |

### 5. `pyproject.toml` (updated)

Added optional test dependencies:
```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
]
```

- `pytest`: Test runner
- `httpx`: Required by FastAPI's TestClient for async HTTP testing

Install with: `uv pip install -e ".[test]"`

## How to run

```bash
# Install test deps
uv pip install -e ".[test]"

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_ingestion.py -v

# Run a specific test
pytest tests/test_ingestion.py::test_clean_text_removes_extra_whitespace -v
```

## Key Takeaways

1. **Tests must be fast** - all 17 tests run in under 2 seconds
2. **Tests must not need secrets** - no API keys required, runs anywhere (local, CI, Docker)
3. **Tests must be deterministic** - same result every time, no randomness
4. **Test the logic, not the API** - we test chunking and formatting, not Pinecone or OpenAI
5. **TestClient is powerful** - test FastAPI endpoints without starting a server
6. **Test pyramid** - lots of unit tests (fast, cheap), fewer integration tests (slower, need APIs)
