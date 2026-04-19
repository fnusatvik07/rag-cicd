# 1. Base image - slim keeps it ~150MB instead of ~1GB
FROM python:3.13-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Install uv (fast package manager)
RUN pip install --no-cache-dir uv

# 4. Copy ONLY dependency file first (layer caching!)
#    If code changes but deps don't, this layer is cached
COPY pyproject.toml .

# 5. Create venv and install deps
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install .

# 6. NOW copy application code (this layer rebuilds on code changes)
COPY app/ app/
COPY main.py .

# 7. Put venv on PATH so python finds our packages
ENV PATH="/app/.venv/bin:$PATH"

# 8. Cloud Run sends traffic to PORT env var (default 8080)
ENV PORT=8080

# 9. Start the server
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port $PORT"]
