"""
Pytest configuration - runs before any test is collected.
Sets dummy env vars so modules that create API clients at import time
don't crash in CI where real keys aren't available.
"""

import os

# Set dummy keys BEFORE any app module is imported
# These are never used for real API calls in unit tests
os.environ.setdefault("PINECONE_API_KEY", "test-dummy-key")
os.environ.setdefault("OPENAI_API_KEY", "test-dummy-key")
