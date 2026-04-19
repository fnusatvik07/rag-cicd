# From Local to Production - RAG Chatbot with Multi-Cloud CI/CD

A complete workshop demonstrating how to take an AI application from local development to production with Docker, automated testing, security scanning, and multi-cloud deployment.

The app is an **Agentic RAG Chatbot** that ingests PDFs, answers questions with inline citations, and decomposes complex queries across multiple documents.

## The Pipeline

```
git push
  |
  +-- Lint (ruff) ............... Code quality check
  +-- Test (pytest) ............. 17 unit tests, no API keys needed
  +-- Security (Snyk + Trivy) ... Dependency + container scanning
  +-- Build Docker image ........ Same image for all clouds
  +-- Deploy
        |
        +-- develop branch --> GCP Cloud Run       (Dev)
        +-- staging branch --> Azure Container Apps (Staging)
        +-- main branch ----> AWS App Runner       (Prod)
        |
        +-- LangSmith traces every LLM call
```

## How This Repo Is Organized

### Incremental Phase Branches

Each phase branch builds on the previous one. Switch between them to see what was added at each step:

```bash
git checkout phase/1-docker       # Adds: Dockerfile, .dockerignore
git checkout phase/2-testing      # Adds: pytest tests (on top of phase 1)
git checkout phase/3-linting      # Adds: ruff config + lint fixes (on top of phase 2)
git checkout phase/4-ci-pipeline  # Adds: GitHub Actions CI (on top of phase 3)
git checkout phase/5-security     # Adds: Snyk + Trivy (on top of phase 4)
git checkout phase/6-environments # Adds: env strategy (on top of phase 5)
git checkout phase/7-deploy       # Adds: Cloud Run CD (on top of phase 6)
git checkout develop              # Everything + multi-cloud + telemetry
```

To see what each phase added:
```bash
git diff phase/1-docker..phase/2-testing --stat
git diff phase/2-testing..phase/3-linting --stat
# ... and so on
```

### Deployment Branches

| Branch | Cloud | Environment | Status |
|--------|-------|-------------|--------|
| `develop` | GCP Cloud Run | Dev | Deployed |
| `staging` | Azure Container Apps | Staging | Deployed |
| `main` | AWS App Runner | Prod | Ready (needs AWS account activation) |

## RAG Architecture

```
INGESTION
  PDF --> Extract text per page --> Chunk (512 chars, 64 overlap) --> Pinecone
                                                                     (server-side embedding)

QUERY
  Question --> Agent Decompose --> Multi-Retrieve --> Rerank --> Generate
               (splits complex      (search per       (BGE-M3)   (gpt-4o-mini
                queries into         sub-query,                    with [1][2]
                sub-queries)         merge results)                citations)
```

**Example:**
```
Q: "Compare Apple and Nike revenue"

Agent decomposes into:
  1. "What was Apple's total revenue?"
  2. "What was Nike's total revenue?"

Retrieves from both documents, merges, reranks, generates:

A: Apple's total net sales were $416.2 billion [1],
   while Nike's total revenues were $46.3 billion [2].

   References:
   [1] Apple_Q24.pdf, p.1
   [2] Nike-Inc-2025_10K.pdf, p.32
```

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/fnusatvik07/rag-cicd.git
cd rag-cicd
uv pip install -e ".[test]"
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
PINECONE_API_KEY=your-pinecone-key
OPENAI_API_KEY=your-openai-key

# Optional: LangSmith telemetry
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=rag-classic-dev
```

### 3. Verify Configuration

```bash
python -m app.config
```

### 4. Ingest Documents and Ask Questions

```bash
python main.py ingest docs/Apple_Q24.pdf
python main.py ingest docs/Nike-Inc-2025_10K.pdf

python main.py ask "What was Apple's revenue in Q4 2024?"
python main.py ask "Compare Apple and Nike revenue" --debug
```

### 5. Start API Server

```bash
python main.py serve
# Swagger UI: http://localhost:8000/docs
```

### 6. Run with Docker

```bash
docker build -t rag-classic .
docker run -p 8080:8080 --env-file .env rag-classic
# Test: curl http://localhost:8080/health
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest` | Ingest a PDF document |
| POST | `/chat` | Agentic RAG: decompose, retrieve, rerank, generate |
| POST | `/generate` | Retrieve, rerank, generate (clean response) |
| POST | `/search` | Search only, no LLM generation |

```bash
# Chat with agentic mode (default)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare Apple and Nike revenue"}'

# Search only (no LLM call)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Nike gross margin", "top_k": 5}'
```

## CI/CD Workflows

| Workflow | File | Trigger | What It Does |
|----------|------|---------|--------------|
| CI: Lint, Test and Build | `ci.yml` | Pull requests | Ruff lint, pytest, Docker build |
| Security: Snyk and Trivy | `security.yml` | Pull requests | Dependency + container vulnerability scanning |
| Deploy: GCP (Dev) | `deploy.yml` | Push to `develop` | Build, push to Artifact Registry, deploy to Cloud Run |
| Deploy: Azure (Staging) | `deploy-azure.yml` | Push to `staging` | Build, push to ACR, deploy to Container Apps |
| Deploy: AWS (Prod) | `deploy-aws.yml` | Push to `main` | Build, push to ECR, deploy to App Runner |

## Project Structure

```
rag-classic/
├── app/
│   ├── config.py              # Settings and environment variables
│   ├── ingestion.py           # PDF text extraction and chunking
│   ├── embedding.py           # Pinecone index creation and upsert
│   ├── retrieval.py           # Semantic search with source diversity
│   ├── reranker.py            # Two-stage reranking with BGE
│   ├── generation.py          # LLM answer generation with citations
│   ├── agent.py               # Query decomposition and multi-retrieve
│   └── api.py                 # FastAPI REST endpoints
├── tests/
│   ├── conftest.py            # Dummy env vars so tests run without API keys
│   ├── test_ingestion.py      # 8 tests: chunking, page tracking, text cleaning
│   ├── test_generation.py     # 4 tests: context formatting, citations
│   └── test_api.py            # 4 tests: health endpoint, request validation
├── .github/workflows/
│   ├── ci.yml                 # CI: lint + test + docker build
│   ├── security.yml           # Security: Snyk + Trivy
│   ├── deploy.yml             # CD: GCP Cloud Run (develop)
│   ├── deploy-azure.yml       # CD: Azure Container Apps (staging)
│   └── deploy-aws.yml         # CD: AWS App Runner (main)
├── Dockerfile                 # Production container with layer caching
├── .dockerignore              # Exclude secrets, IDE files, tests from image
├── pyproject.toml             # Dependencies + ruff linter config
├── .env.example               # Template for environment variables
├── main.py                    # CLI: ingest / ask / serve
└── rag_test.py                # Step-by-step pipeline walkthrough (learning tool)
```

## Documentation

### Cloud Deployment Guides

Step-by-step setup from creating a cloud account to seeing the app live:

| Guide | Cloud | What It Covers |
|-------|-------|---------------|
| [DEPLOY-SETUP-GUIDE.md](DEPLOY-SETUP-GUIDE.md) | GCP (detailed) | Project setup, APIs, service account, roles, JSON key, GitHub Secrets, troubleshooting |
| [GCP-SETUP-GUIDE.md](GCP-SETUP-GUIDE.md) | GCP (summary) | Quick reference for Cloud Run deployment |
| [AZURE-SETUP-GUIDE.md](AZURE-SETUP-GUIDE.md) | Azure | Resource group, ACR, service principal, Container Apps |
| [AWS-SETUP-GUIDE.md](AWS-SETUP-GUIDE.md) | AWS | IAM user, ECR, App Runner |

### Phase Explainer Docs

Each phase has a detailed doc explaining what was added and why:

| Phase | Topic | Doc |
|-------|-------|-----|
| 1 | Docker - containerization | [PHASE1-DOCKER.md](PHASE1-DOCKER.md) |
| 2 | Testing - pytest unit tests | [PHASE2-TESTING.md](PHASE2-TESTING.md) |
| 3 | Linting - ruff code quality | [PHASE3-LINTING.md](PHASE3-LINTING.md) |
| 4 | CI Pipeline - GitHub Actions | [PHASE4-CI-PIPELINE.md](PHASE4-CI-PIPELINE.md) |
| 5 | Security - Snyk + Trivy | [PHASE5-SECURITY.md](PHASE5-SECURITY.md) |
| 6 | Environments - dev/staging/prod | [PHASE6-ENVIRONMENTS.md](PHASE6-ENVIRONMENTS.md) |
| 7 | Deployment - Cloud Run CD | [PHASE7-DEPLOY.md](PHASE7-DEPLOY.md) |
| 8 | Telemetry - LangSmith | [PHASE8-TELEMETRY.md](PHASE8-TELEMETRY.md) |

### Production Topics

| Doc | Topics Covered |
|-----|---------------|
| [BEYOND-CLASS.md](BEYOND-CLASS.md) | Kubernetes vs serverless, rate limiting, traffic management (blue/green, canary), authentication, observability stack, Infrastructure as Code (Terraform), database migrations, AI-specific production concerns |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| API Framework | FastAPI |
| Vector Database | Pinecone (serverless, integrated embedding) |
| Embedding Model | multilingual-e5-large (server-side) |
| Reranker | bge-reranker-v2-m3 (server-side) |
| LLM | OpenAI gpt-4o-mini via LangChain |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Security Scanning | Snyk (dependencies) + Trivy (container) |
| Linting | Ruff |
| Testing | pytest (17 tests, no API keys needed) |
| Observability | LangSmith (zero code changes) |
| Dev Cloud | GCP Cloud Run |
| Staging Cloud | Azure Container Apps |
| Prod Cloud | AWS App Runner |
