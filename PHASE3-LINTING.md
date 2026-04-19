# Phase 3 - Linting

## What is Linting?

Linting is automated code quality checking. A linter reads your code and flags problems like:
- Unused imports (you imported something but never used it)
- Undefined variables (typos in variable names)
- Wrong import order (messy imports)
- Deprecated syntax (old Python patterns that have better modern alternatives)
- Style violations (inconsistent whitespace, line too long)

Think of it as a spell checker for code. It catches bugs and enforces consistency before code even runs.

## What is Ruff?

Ruff is a fast Python linter written in Rust. It replaces multiple older tools:

| Old Tool | What it did | Ruff replaces it? |
|----------|-------------|-------------------|
| flake8 | Style checking | Yes |
| isort | Import sorting | Yes |
| black | Code formatting | Yes |
| pyupgrade | Modernize syntax | Yes |

Ruff does all of this in one tool and is 10-100x faster than running them separately.

## What was added

### `pyproject.toml` - Ruff configuration

```toml
[tool.ruff]
line-length = 120             # max characters per line
target-version = "py313"      # Python version we're targeting
```
- `line-length = 120`: default is 88, we use 120 for readability
- `target-version`: tells ruff which Python features are available

```toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors (missing whitespace, wrong indentation)
    "W",    # pycodestyle warnings (trailing whitespace, blank lines)
    "F",    # pyflakes (unused imports, undefined names)
    "I",    # isort (import ordering)
    "UP",   # pyupgrade (use modern Python syntax)
]
```
Each letter is a rule set:
- **E/W**: Basic style (PEP 8 compliance)
- **F**: Logic errors (unused imports, undefined variables - these catch real bugs)
- **I**: Import ordering (stdlib first, then third-party, then local)
- **UP**: Modernize code (e.g., `List[str]` -> `list[str]` in Python 3.9+)

```toml
ignore = ["E501"]  # line too long - handled by line-length setting
```

```toml
[tool.ruff.lint.isort]
known-first-party = ["app"]   # our app/ is first-party, not third-party
```
This ensures `from app.config import ...` is grouped separately from `from fastapi import ...`.

```toml
[tool.ruff.lint.per-file-ignores]
"rag_test.py" = ["E402"]      # walkthrough script has imports mid-file by design
```
Some files intentionally break rules. `rag_test.py` imports modules in the middle of the file because it's a step-by-step walkthrough script.

## What Ruff fixed in our code (89 issues)

| Issue | Count | Example |
|-------|-------|---------|
| Unsorted imports | 8 | `import sys, import os` reordered to `import os, import sys` |
| `List[str]` -> `list[str]` | 30+ | Modern Python 3.9+ syntax, no need for `from typing import List` |
| `Optional[str]` -> `str \| None` | 5 | Modern Python 3.10+ union syntax |
| Unused imports | 4 | `TEMPERATURE` imported but never used in agent.py |
| f-string without placeholders | 4 | `f"hello"` -> `"hello"` (no variables to interpolate) |
| `from typing import List, Dict` removed | 6 | Not needed in Python 3.13, built-in types work directly |

## How to run

```bash
# Install ruff
uv pip install ruff

# Check for issues (report only)
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code (like black)
ruff format .

# Check a specific file
ruff check app/agent.py
```

## Why this matters for CI/CD

In the next phase, we add ruff to the GitHub Actions pipeline. If linting fails, the build fails and code cannot be deployed. This means:
- No unused imports accumulating over time
- Consistent code style across the team
- Deprecated patterns get upgraded automatically
- Typos in variable names caught before runtime

## Key Takeaways

1. **Linting catches bugs before they run** - unused imports, undefined names, typos
2. **Ruff replaces 4+ tools** - flake8, isort, black, pyupgrade in one fast tool
3. **Config lives in pyproject.toml** - everyone on the team uses the same rules
4. **Auto-fix saves time** - `ruff check --fix` fixes most issues automatically
5. **Per-file ignores** - some files intentionally break rules, and that's OK
6. **This becomes a CI gate** - fail lint = fail build = no deploy
