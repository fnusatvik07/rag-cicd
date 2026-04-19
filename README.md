# RAG Classic - Agentic RAG Chatbot with CI/CD

A production-ready RAG chatbot with a complete CI/CD pipeline deploying to **GCP**, **Azure**, and **AWS**.

Built with **Pinecone**, **LangChain**, **FastAPI**, and an **agentic pipeline** that decomposes complex queries into sub-queries for multi-source retrieval.

## What This Repo Demonstrates

```
Developer writes code
  -> git push
    -> GitHub Actions
      -> Lint (ruff)
      -> Test (pytest)
      -> Security scan (Snyk + Trivy)
      -> Build Docker image
      -> Push to container registry
      -> Deploy to cloud
        -> develop  -> GCP Cloud Run      (Dev)
        -> staging  -> Azure Container Apps (Staging)
        -> main     -> AWS App Runner      (Prod)
      -> LangSmith traces every LLM call
```

## Architecture

```
INGESTION: PDF -> Page Extraction -> Chunking -> Pinecone (integrated embedding)

QUERY:     Question -> Agent Decompose -> Multi-Retrieve -> Rerank -> Generate Answer
```

| Stage | What | Model / Service |
|-------|------|-----------------|
| Ingestion | PDF text extraction + chunking | pypdf |
| Embedding | Server-side embedding | Pinecone multilingual-e5-large |
| Decomposition | Break complex queries into sub-queries | OpenAI gpt-4o-mini |
| Retrieval | Semantic search with source diversity | Pinecone integrated search |
| Reranking | Re-order by relevance | Pinecone bge-reranker-v2-m3 |
| Generation | Answer with inline citations | LangChain ChatOpenAI |

## Project Structure

```
rag-classic/
├── app/
│   ├── config.py          # Settings and env vars
│   ├── ingestion.py       # PDF loading, chunking
│   ├── embedding.py       # Pinecone index and upsert
│   ├── retrieval.py       # Semantic search with source diversity
│   ├── reranker.py        # Two-stage reranking
│   ├── generation.py      # LLM answer with citations
│   ├── agent.py           # Agentic query decomposition
│   └── api.py             # FastAPI endpoints
├── tests/
│   ├── conftest.py        # Dummy env vars for CI
│   ├── test_ingestion.py  # 8 tests
│   ├── test_generation.py # 4 tests
│   └── test_api.py        # 4 tests (no API keys needed)
├── .github/workflows/
│   ├── ci.yml             # Lint + Test + Docker build (PRs)
│   ├── security.yml       # Snyk + Trivy (PRs)
│   ├── deploy.yml         # GCP Cloud Run (develop branch)
│   ├── deploy-azure.yml   # Azure Container Apps (staging branch)
│   └── deploy-aws.yml     # AWS App Runner (main branch)
├── Dockerfile             # Production container
├── pyproject.toml         # Dependencies + ruff config
├── main.py                # CLI: ingest / ask / serve
└── rag_test.py            # Step-by-step pipeline walkthrough
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/fnusatvik07/rag-cicd.git
cd rag-cicd
uv pip install -e ".[test]"

# Add API keys
cp .env.example .env
# Edit .env with your PINECONE_API_KEY and OPENAI_API_KEY

# Ingest documents
python main.py ingest docs/Apple_Q24.pdf
python main.py ingest docs/Nike-Inc-2025_10K.pdf

# Ask questions
python main.py ask "What was Apple's revenue in Q4 2024?"
python main.py ask "Compare Apple and Nike revenue"

# Start API server
python main.py serve
# Open http://localhost:8000/docs for Swagger UI
```

## CI/CD Pipeline

### Workflows

| Workflow | Triggers On | What It Does |
|----------|------------|--------------|
| CI: Lint, Test and Build | Pull requests | Ruff lint, pytest, Docker build |
| Security: Snyk and Trivy | Pull requests | Dependency and container scanning |
| Deploy: GCP (Dev) | Push to develop | Build, push to Artifact Registry, deploy to Cloud Run |
| Deploy: Azure (Staging) | Push to staging | Build, push to ACR, deploy to Container Apps |
| Deploy: AWS (Prod) | Push to main | Build, push to ECR, deploy to App Runner |

### Branch Strategy

```
feature/* -> develop -> staging -> main
               |          |         |
              Dev      Staging    Prod
             (GCP)    (Azure)    (AWS)
```

### Environment-Based Config

Same Docker image, different configuration per environment:

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| Cloud | GCP Cloud Run | Azure Container Apps | AWS App Runner |
| LangSmith Project | rag-classic-dev | rag-classic-staging | rag-classic-prod |
| Pinecone Index | rag-classic-dev | rag-classic-staging | rag-classic |

## Observability

LangSmith traces every LLM call with zero code changes:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=rag-classic-dev
```

Traces show: query decomposition, retrieval, reranking, generation, token usage, latency, and cost.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /ingest | Ingest a document (PDF/TXT) |
| POST | /chat | Agentic RAG pipeline (decompose, retrieve, rerank, generate) |
| POST | /generate | Retrieve, rerank, generate (clean response) |
| POST | /search | Search only (no LLM generation) |

## Documentation

| Guide | What It Covers |
|-------|---------------|
| [GCP Setup Guide](GCP-SETUP-GUIDE.md) | Cloud Run deployment from scratch |
| [Azure Setup Guide](AZURE-SETUP-GUIDE.md) | Container Apps deployment from scratch |
| [AWS Setup Guide](AWS-SETUP-GUIDE.md) | App Runner deployment from scratch |
| [Beyond Class](BEYOND-CLASS.md) | Kubernetes, rate limiting, IaC, monitoring |

### Phase-by-Phase Explainers

Each phase branch has a detailed explainer doc:

| Phase | Branch | Doc | Topic |
|-------|--------|-----|-------|
| 1 | phase/1-docker | [PHASE1-DOCKER.md](PHASE1-DOCKER.md) | Dockerfile from scratch |
| 2 | phase/2-testing | [PHASE2-TESTING.md](PHASE2-TESTING.md) | pytest unit tests |
| 3 | phase/3-linting | [PHASE3-LINTING.md](PHASE3-LINTING.md) | Ruff linter setup |
| 4 | phase/4-ci-pipeline | [PHASE4-CI-PIPELINE.md](PHASE4-CI-PIPELINE.md) | GitHub Actions CI |
| 5 | phase/5-security | [PHASE5-SECURITY.md](PHASE5-SECURITY.md) | Snyk + Trivy scanning |
| 6 | phase/6-environments | [PHASE6-ENVIRONMENTS.md](PHASE6-ENVIRONMENTS.md) | Environment strategy |
| 7 | phase/7-deploy | [PHASE7-DEPLOY.md](PHASE7-DEPLOY.md) | Cloud Run deployment |
| 8 | - | [PHASE8-TELEMETRY.md](PHASE8-TELEMETRY.md) | LangSmith observability |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| API Framework | FastAPI |
| Vector Database | Pinecone (serverless) |
| Embedding | Pinecone multilingual-e5-large (server-side) |
| Reranker | Pinecone bge-reranker-v2-m3 |
| LLM | OpenAI gpt-4o-mini via LangChain |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Security | Snyk (dependencies) + Trivy (container) |
| Observability | LangSmith |
| Linting | Ruff |
| Testing | pytest |
