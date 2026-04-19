# Phase 1 - Docker

## What was added

Two files were created from scratch to containerize the RAG application.

## Files Added

### 1. `.dockerignore`

Tells Docker which files to exclude when building the image.

```
.git           # Git history is not needed inside the container
.gitignore     # Git config not needed at runtime
.env           # NEVER put secrets in the image, pass them at runtime via -e flag
.venv          # Local virtual env, container builds its own
__pycache__    # Python bytecode cache, regenerated inside container
*.pyc          # Compiled Python files
*.pyo          # Optimized Python files
.DS_Store      # macOS filesystem metadata
.idea          # JetBrains IDE config
.vscode        # VS Code config
*.egg-info     # Python package metadata
rag_test.py    # Test walkthrough script, not needed in production
README.md      # Documentation, not needed at runtime
plan.md        # Class planning file
```

**Why this matters**:
- Smaller image size (faster builds, faster deploys)
- Security: `.env` with API keys never ends up in the image
- Cleanliness: no IDE junk or test files in production

### 2. `Dockerfile`

Blueprint for building a container image of the app.

```dockerfile
FROM python:3.13-slim
```
**Why slim?** The full `python:3.13` image is ~1GB. The slim variant is ~150MB. It strips out compilers, docs, and dev tools we don't need at runtime.

```dockerfile
WORKDIR /app
```
All subsequent commands run inside `/app` in the container. Keeps things organized.

```dockerfile
RUN pip install --no-cache-dir uv
```
Install `uv`, a fast Python package manager. `--no-cache-dir` avoids storing pip's download cache (saves ~50MB in the image).

```dockerfile
COPY pyproject.toml .
RUN uv venv /app/.venv && . /app/.venv/bin/activate && uv pip install .
```
**This is the most important Docker optimization: layer caching.**
- Docker caches each layer (each instruction).
- By copying `pyproject.toml` FIRST and installing deps BEFORE copying app code, Docker reuses the cached dependency layer when only code changes.
- Without this, every code change would reinstall all dependencies (~30-60 seconds wasted per build).

```dockerfile
COPY app/ app/
COPY main.py .
COPY docs/ docs/
```
Copy application code AFTER dependencies. This layer rebuilds on every code change, but deps layer stays cached.

**Rule of thumb**: Things that change LEAST go first, things that change MOST go last.

```dockerfile
ENV PATH="/app/.venv/bin:$PATH"
```
Puts the virtual environment on the system PATH so `python` and `uvicorn` resolve to the venv versions with all our packages installed.

```dockerfile
ENV PORT=8080
```
Cloud Run (and many cloud platforms) inject a `PORT` environment variable. Default to 8080 so the container works locally too.

```dockerfile
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port $PORT"]
```
Start the FastAPI server:
- `--host 0.0.0.0`: Listen on all interfaces (required for containers, otherwise it only listens on localhost which is unreachable from outside the container)
- `--port $PORT`: Use the PORT env var so Cloud Run can control which port to use
- `sh -c` is needed to expand the `$PORT` variable at runtime

## Testing Checklist

Make sure Docker Desktop is running before starting.

### Step 1: Build the image

```bash
docker build -t rag-classic .
```

**What to verify**:
- [ ] Build completes without errors
- [ ] Each step shows "CACHED" on subsequent builds (layer caching works)
- [ ] No `.env` file or secrets in the build output

### Step 2: Check the image

```bash
docker images rag-classic
```

**What to verify**:
- [ ] Image exists in the list
- [ ] Image size is under 300MB (slim base image working)

### Step 3: Run the container

```bash
docker run -d --name rag-test -p 8080:8080 --env-file .env rag-classic
```

**What to verify**:
- [ ] Container starts without crashing
- [ ] Check logs: `docker logs rag-test` shows uvicorn startup message

### Step 4: Test the endpoints

```bash
# Health check
curl http://localhost:8080/health

# Swagger docs (open in browser)
open http://localhost:8080/docs

# Chat endpoint
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in Q4 2024?"}'

# Search endpoint (no LLM call, faster)
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Nike revenue", "top_k": 3}'
```

**What to verify**:
- [ ] `/health` returns `{"status": "ok"}`
- [ ] `/docs` loads Swagger UI in browser
- [ ] `/chat` returns an answer with sources and citations
- [ ] `/search` returns search results with scores

### Step 5: Verify .dockerignore is working

```bash
# Shell into the running container and check no secrets leaked
docker exec rag-test ls -la /app/

# These should NOT exist inside the container:
docker exec rag-test cat /app/.env 2>&1        # Should say "No such file"
docker exec rag-test ls /app/.git 2>&1         # Should say "No such file"
docker exec rag-test ls /app/.venv 2>&1        # Should say "No such file"
docker exec rag-test cat /app/rag_test.py 2>&1 # Should say "No such file"
```

**What to verify**:
- [ ] `.env` is NOT in the container
- [ ] `.git` is NOT in the container
- [ ] `.venv` is NOT in the container
- [ ] `rag_test.py` is NOT in the container
- [ ] Only `app/`, `main.py`, `docs/`, `pyproject.toml` are present

### Step 6: Test layer caching

```bash
# Make a small code change (add a comment to main.py)
echo "# test" >> main.py

# Rebuild - deps layer should say CACHED
docker build -t rag-classic .

# Undo the change
git checkout main.py
```

**What to verify**:
- [ ] Steps 1-5 (base image, uv install, deps) show "CACHED"
- [ ] Only step 6 (COPY app code) rebuilds
- [ ] Rebuild takes seconds, not minutes

### Step 7: Cleanup

```bash
# Stop and remove container
docker stop rag-test
docker rm rag-test

# Remove image (optional)
docker rmi rag-classic
```

## Key Takeaways

1. **Docker solves "works on my machine"** - same image runs on any machine, any cloud
2. **Layer caching is critical** - copy deps before code to avoid slow rebuilds
3. **Never put secrets in images** - use `.dockerignore` for `.env`, pass secrets via `-e` at runtime
4. **Use slim base images** - saves hundreds of MBs, fewer vulnerabilities
5. **If it runs in Docker, it runs anywhere** - GCP, AWS, Azure, your laptop
