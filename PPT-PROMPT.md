# Prompt for AI Slide Generator

Copy the entire prompt below and paste it into an AI presentation tool (Gamma.app, Beautiful.ai, ChatGPT with slide plugins, or Google Slides + Gemini).

---

## PROMPT START

Create a professional, visually polished presentation with the following specifications:

### Design Requirements
- Style: Modern, minimal, enterprise-grade. Think McKinsey or Google Cloud consulting decks.
- Color scheme: Dark navy (#1a1a2e) backgrounds with white text and accent colors (electric blue #0066ff, green #00c853 for success states, orange #ff6d00 for warnings).
- Typography: Clean sans-serif (Inter, Helvetica, or similar). Titles bold, body regular.
- Icons: Use simple line icons for each concept. No clip art.
- Diagrams: Use clean flowcharts, architecture diagrams, and comparison tables. No stock photos.
- Layout: One key idea per slide. No walls of text. Use bullet points sparingly.
- Total slides: 45-50 slides
- Aspect ratio: 16:9

---

### TITLE SLIDE (Slide 1)
**Title**: From Local to Production: Deploying AI Applications at Scale
**Subtitle**: A Complete CI/CD Workshop — Docker, Testing, Security, Multi-Cloud Deployment & Observability
**Footer**: Workshop Duration: 2 Hours | Hands-On + Conceptual

---

### SECTION 1: THE BIG PICTURE (Slides 2-6)

**Slide 2 — The Problem**
Title: "It Works on My Machine"
Content: Show the classic developer scenario:
- Developer writes code on laptop, everything works
- Pushes to production, everything breaks
- Root causes: different Python versions, missing dependencies, environment mismatches, secrets management
- Visual: Split screen — happy developer on left, burning server on right

**Slide 3 — The Solution: CI/CD Pipeline**
Title: What is CI/CD?
Content:
- CI (Continuous Integration): Automatically validate code on every push — lint, test, build
- CD (Continuous Deployment): Automatically deploy validated code to production
- Key principle: "If it's not automated, it's not reliable"
- Visual: Linear pipeline diagram:
  ```
  Code Push → Lint → Test → Security Scan → Build Image → Push to Registry → Deploy
  ```

**Slide 4 — The Journey We'll Build**
Title: From Local to Production in 8 Phases
Content: Numbered roadmap with icons:
1. Docker — Containerize the app
2. Testing — Automated quality gates
3. Linting — Code consistency
4. CI Pipeline — GitHub Actions automation
5. Security — Vulnerability scanning
6. Environments — Dev / QA / Staging / Prod
7. Deployment — Multi-cloud CD
8. Observability — LLM telemetry and monitoring

**Slide 5 — The App We're Deploying**
Title: RAG Chatbot Architecture
Content: Architecture diagram showing:
- Ingestion: PDF → Page Extraction → Chunking → Pinecone (with integrated embedding)
- Query: Question → Agent Decomposition → Multi-Retrieve → Rerank → LLM Generate → Cited Answer
- Tech stack: FastAPI, Pinecone, LangChain, OpenAI, Python 3.13
- Endpoints: /health, /ingest, /chat, /search, /generate

**Slide 6 — What Production Means**
Title: Local vs Production — The Gap
Content: Comparison table:
| Aspect | Local Development | Production |
|--------|------------------|------------|
| Environment | Your laptop | Cloud servers |
| Dependencies | "pip install" | Docker container |
| Secrets | .env file | Secret managers |
| Testing | "I ran it once" | Automated test suite |
| Scaling | 1 user (you) | Thousands of users |
| Monitoring | print() statements | Observability platform |
| Deployment | "python main.py" | Automated CD pipeline |
| Rollback | Ctrl+Z | Container revisions |

---

### SECTION 2: DOCKER — CONTAINERIZATION (Slides 7-12)

**Slide 7 — Section Divider**
Title: Phase 1: Docker
Subtitle: "Package Once, Run Anywhere"
Visual: Docker whale icon

**Slide 8 — What is Docker?**
Title: Containers vs Virtual Machines
Content:
- Container: Lightweight, shares OS kernel, starts in seconds, ~150MB
- Virtual Machine: Heavy, includes full OS, starts in minutes, ~5GB
- Docker packages your app + all dependencies into a single image
- Same image runs on: your laptop, CI server, GCP, AWS, Azure
- Visual: Side-by-side diagram of container stack vs VM stack

**Slide 9 — Dockerfile Anatomy**
Title: Building the Container — Line by Line
Content: Show annotated Dockerfile:
```dockerfile
FROM python:3.13-slim          # Base image (150MB vs 1GB)
WORKDIR /app                   # Working directory
RUN pip install uv             # Package manager
COPY pyproject.toml .          # Dependencies FIRST (layer caching!)
RUN uv pip install .           # Install dependencies
COPY app/ app/                 # Application code LAST
COPY main.py .                 # Entry point
ENV PORT=8080                  # Cloud Run convention
CMD ["uvicorn", "app.api:app"] # Start server
```

**Slide 10 — Layer Caching**
Title: The Most Important Docker Optimization
Content:
- Docker caches each layer (each instruction)
- If a layer hasn't changed, Docker reuses the cached version
- Order matters: things that change LEAST go first
- Dependencies change rarely → copy first → cached
- App code changes often → copy last → only this rebuilds
- Visual: Two build timelines — without caching (60s) vs with caching (3s)

**Slide 11 — .dockerignore**
Title: What NOT to Put in Your Image
Content:
- .env → NEVER put secrets in images
- .git → History not needed at runtime
- .venv → Container builds its own
- __pycache__ → Regenerated inside container
- test files → Not needed in production
- Rule: If it's not needed to RUN the app, exclude it

**Slide 12 — Docker Commands**
Title: Build, Run, Test
Content:
```bash
docker build -t my-app .                    # Build image
docker run -p 8080:8080 --env-file .env my-app  # Run container
curl http://localhost:8080/health            # Test it
docker images my-app                         # Check size
docker exec my-app ls /app/.env              # Verify no secrets
```

---

### SECTION 3: TESTING (Slides 13-17)

**Slide 13 — Section Divider**
Title: Phase 2: Testing
Subtitle: "The Gate That Prevents Broken Code"

**Slide 14 — The Test Pyramid**
Title: Types of Tests
Content: Pyramid diagram:
- Top (few): E2E Tests — Test full user flows, slow, expensive
- Middle (some): Integration Tests — Test components together, need APIs
- Bottom (many): Unit Tests — Test individual functions, fast, no dependencies
- We focus on unit tests: fast, free, run anywhere, no API keys needed

**Slide 15 — What We Test**
Title: 17 Tests, Zero API Keys
Content: Three test files:
| File | Tests | What It Validates |
|------|-------|------------------|
| test_ingestion.py | 8 | Chunking logic, page tracking, text cleaning |
| test_generation.py | 4 | Context formatting, citation numbering |
| test_api.py | 4 | Health endpoint, request validation |
- All 17 tests run in under 2 seconds
- No Pinecone or OpenAI keys needed

**Slide 16 — conftest.py: The CI Secret**
Title: Making Tests Work Without API Keys
Content:
- Problem: App creates Pinecone/OpenAI clients at import time
- In CI, there are no .env files with real keys
- Solution: conftest.py sets dummy env vars BEFORE imports
- Tests never make real API calls — they test logic only
```python
import os
os.environ.setdefault("PINECONE_API_KEY", "test-dummy-key")
os.environ.setdefault("OPENAI_API_KEY", "test-dummy-key")
```

**Slide 17 — Test Rules**
Title: Good Tests Are...
Content:
- Fast — All tests under 5 seconds total
- Deterministic — Same result every time
- Independent — No test depends on another
- No external dependencies — No API calls, no database
- Descriptive names — test_chunk_pages_tracks_page_numbers

---

### SECTION 4: LINTING (Slides 18-20)

**Slide 18 — Section Divider**
Title: Phase 3: Linting
Subtitle: "Spell Check for Code"

**Slide 19 — What is Linting?**
Title: Automated Code Quality
Content:
- Finds: unused imports, undefined variables, deprecated syntax, style violations
- Ruff: One tool that replaces flake8 + isort + black + pyupgrade
- 10-100x faster than running them separately (written in Rust)
- Auto-fix: `ruff check --fix` fixes most issues automatically
- We found and fixed 89 issues in our codebase

**Slide 20 — Ruff Configuration**
Title: pyproject.toml — Rules Everyone Follows
Content:
```toml
[tool.ruff.lint]
select = [
    "E",    # Style errors
    "W",    # Style warnings  
    "F",    # Logic errors (unused imports, undefined names)
    "I",    # Import ordering
    "UP",   # Modern Python syntax
]
```
Key point: Config is in the repo, so every developer and CI uses the same rules.

---

### SECTION 5: CI PIPELINE (Slides 21-25)

**Slide 21 — Section Divider**
Title: Phase 4: CI Pipeline
Subtitle: "Automated Quality Gates with GitHub Actions"

**Slide 22 — What is GitHub Actions?**
Title: CI/CD Built Into GitHub
Content:
- Workflow: YAML file in .github/workflows/
- Trigger: push, pull_request, schedule, manual
- Runner: Fresh Ubuntu VM that GitHub provides (free for public repos)
- Every push gets validated automatically — no one needs to remember

**Slide 23 — The Pipeline**
Title: 6 Steps, 3 Quality Gates
Content: Pipeline diagram with gates:
```
Checkout → Setup Python → Install Deps → [GATE] Lint → [GATE] Test → [GATE] Docker Build
                                           ↓ fail        ↓ fail        ↓ fail
                                          STOP           STOP          STOP
```
If any gate fails, pipeline stops. Nothing deploys.

**Slide 24 — Where Does the Docker Image Go?**
Title: CI vs CD — Build vs Deploy
Content:
- Phase 4 (CI): Build image → verify it works → discard (runner dies)
- Phase 7 (CD): Build image → push to registry → deploy to cloud
- CI catches Dockerfile errors early, before attempting to deploy
- Visual: Two paths — CI (build → trash) vs CD (build → registry → cloud)

**Slide 25 — Branch Protection**
Title: PRs Can't Merge If CI Fails
Content:
- GitHub shows CI status directly on the PR page
- Green checkmark: tests pass, safe to merge
- Red X: tests fail, merge blocked
- Reviewers see code quality before approving
- Visual: Screenshot-style of PR with CI checks

---

### SECTION 6: SECURITY (Slides 26-30)

**Slide 26 — Section Divider**
Title: Phase 5: Security Scanning
Subtitle: "Your Code is Only as Secure as Your Dependencies"

**Slide 27 — Why Security Scanning?**
Title: The Supply Chain Risk
Content:
- Your app has ~57 Python packages installed
- Each maintained by someone else
- One vulnerable dependency = potential breach
- Example: A single compromised npm package affected 50,000+ projects
- Shift Left: Catch vulnerabilities in CI, not after deployment

**Slide 28 — Three Layers of Scanning**
Title: What We Scan
Content: Three columns:
| Layer | Tool | What It Finds |
|-------|------|--------------|
| Python packages | Snyk | Known CVEs in pip dependencies |
| Docker image | Trivy | OS-level vulnerabilities in base image |
| Source code | SonarQube* | Bugs, code smells, security hotspots |
*Conceptual — not implemented in this workshop but used in enterprise

**Slide 29 — OWASP Top 10**
Title: The 10 Most Common Security Risks
Content: Numbered list with icons:
1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, command)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components ← Our scanning addresses this
7. Authentication Failures
8. Data Integrity Failures
9. Logging Failures
10. SSRF
Our security scanning directly addresses #6.

**Slide 30 — Severity Levels**
Title: Not All Vulnerabilities Are Equal
Content:
| Level | Action | Example |
|-------|--------|---------|
| Critical | Fix immediately | Remote code execution |
| High | Fix before deploy | Data exposure |
| Medium | Plan to fix | Requires specific conditions |
| Low | Monitor | Hard to exploit |
We set --severity-threshold=high: block on HIGH/CRITICAL, report the rest.

---

### SECTION 7: ENVIRONMENTS (Slides 31-35)

**Slide 31 — Section Divider**
Title: Phase 6: Environments
Subtitle: "Dev → QA → Staging → Production"

**Slide 32 — The Four Environments**
Title: Each Is a Safety Net
Content: Flow diagram:
```
Dev → QA → Staging → Production
Auto-deploy   QA team    Mirror of    Real users
on push       tests      prod
Can break     Should be   Must be     Must be
              stable      stable      rock solid
```
The further right a bug travels, the more expensive it is to fix.

**Slide 33 — Same Image, Different Config**
Title: What Changes Between Environments?
Content:
| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| Index name | rag-classic-dev | rag-classic-staging | rag-classic |
| API keys | Dev keys | Staging keys | Prod keys |
| LLM model | gpt-4o-mini | gpt-4o-mini | gpt-4o |
| Instances | 0-1 | 0-1 | 2-10 |
| Cloud | GCP | Azure | AWS |
Key principle: NEVER rebuild code per environment. Same Docker image everywhere.

**Slide 34 — Branch Strategy**
Title: Branches Map to Environments
Content:
```
feature/* → develop → staging → main
              ↓          ↓        ↓
             Dev      Staging    Prod
             (GCP)    (Azure)   (AWS)
             Auto     Auto     Approval required
```

**Slide 35 — Secrets Management**
Title: Secrets Never Live in Code
Content: Flow diagram:
```
Developer → .env file (gitignored, local only)
CI/CD     → GitHub Secrets (encrypted, per environment)
Cloud     → Environment variables (injected at runtime)
Enterprise → HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager
```

---

### SECTION 8: DEPLOYMENT (Slides 36-41)

**Slide 36 — Section Divider**
Title: Phase 7: Cloud Deployment
Subtitle: "One Push, Three Clouds"

**Slide 37 — Multi-Cloud Architecture**
Title: Our Deployment Setup
Content: Architecture diagram:
```
GitHub Repository
  |
  ├── develop → GCP Cloud Run (Dev)
  |              Artifact Registry → Cloud Run
  |
  ├── staging → Azure Container Apps (Staging)
  |              ACR → Container Apps
  |
  └── main → AWS App Runner (Prod)
               ECR → App Runner
```
Same Docker image deployed to all three clouds.

**Slide 38 — The CD Pipeline**
Title: What Happens on git push?
Content: Detailed flow:
```
git push to develop
  → GitHub Actions triggers
    → Lint (ruff check .)           [2s]
    → Test (pytest tests/)          [2s]
    → Build Docker image            [15s]
    → Push to Artifact Registry     [10s]
    → Deploy to Cloud Run           [60s]
    → App is live at URL
  Total: ~90 seconds from push to production
```

**Slide 39 — Cloud Comparison**
Title: Three Clouds, Same Pattern
Content:
| Step | GCP | AWS | Azure |
|------|-----|-----|-------|
| Image Storage | Artifact Registry | ECR | ACR |
| Compute | Cloud Run | App Runner | Container Apps |
| Auth | Service Account | IAM User | Service Principal |
| Scale to zero | Yes | Yes | Yes |
| Deploy command | gcloud run deploy | aws apprunner create | az containerapp create |
The Docker image is identical. Only deployment commands differ.

**Slide 40 — Rollback Strategies**
Title: When Things Go Wrong
Content:
| Strategy | How | Downtime | Complexity |
|----------|-----|----------|------------|
| Git revert + redeploy | Revert commit, CI/CD redeploys | Minutes | Low |
| Cloud revision rollback | Route traffic to previous version | Seconds | Low |
| Blue/Green | Two environments, swap traffic | Zero | Medium |
| Canary | 5% to new, 95% to old, observe | Zero | High |
Cloud Run, App Runner, Container Apps all support revision-based rollback.

**Slide 41 — Infrastructure as Code**
Title: Beyond Click-Ops (Enterprise Level)
Content:
- What we did: Clicked through GCP/Azure/AWS consoles
- Enterprise approach: Define infrastructure in code (Terraform, Pulumi)
- Benefits: Version controlled, reproducible, reviewable in PRs
```hcl
resource "google_cloud_run_service" "rag" {
  name     = "rag-classic"
  location = "us-central1"
  template {
    spec {
      containers {
        image = "us-central1-docker.pkg.dev/project/repo/rag:latest"
      }
    }
  }
}
```

---

### SECTION 9: OBSERVABILITY (Slides 42-45)

**Slide 42 — Section Divider**
Title: Phase 8: Observability
Subtitle: "You Can't Fix What You Can't See"

**Slide 43 — LangSmith for LLM Apps**
Title: Tracing the Full RAG Chain
Content: Trace visualization:
```
/chat "Compare Apple and Nike revenue"  [2.4s total]
  ├── decompose_query              [120ms | 85 tokens]
  ├── search("Apple revenue")      [340ms]
  ├── search("Nike revenue")       [280ms]
  ├── rerank                       [450ms]
  └── ChatOpenAI.invoke            [1.2s | 350 tokens | $0.0004]
```
- Zero code changes: just 3 env vars
- See every prompt, response, token count, and cost
- Debug bad answers by clicking on the trace

**Slide 44 — What to Monitor in Production**
Title: Key Metrics for AI Applications
Content:
| Metric | Why | Alert When |
|--------|-----|-----------|
| Request latency (p95) | User experience | > 5 seconds |
| Error rate (5xx) | App is broken | > 1% |
| Token usage/day | Cost control | > daily budget |
| Cold start time | First request delay | > 10 seconds |
| Retrieval relevance | RAG quality | Score < 0.5 |
| Memory usage | OOM crashes | > 80% |
| LLM hallucination rate | Answer quality | Manual review |

**Slide 45 — Observability Stack**
Title: Tools for Different Layers
Content:
| Layer | Tool | What It Monitors |
|-------|------|-----------------|
| LLM Chains | LangSmith / Langfuse | Prompts, tokens, latency, cost |
| Application | Datadog / New Relic | Request traces, errors, APM |
| Infrastructure | CloudWatch / Cloud Monitoring | CPU, memory, network |
| Uptime | PagerDuty / OpsGenie | Alerting, on-call rotation |
| Logs | ELK Stack / Cloud Logging | Searchable log aggregation |

---

### SECTION 10: ENTERPRISE CONSIDERATIONS (Slides 46-49)

**Slide 46 — Section Divider**
Title: Beyond the Workshop
Subtitle: "What Enterprise Production Really Looks Like"

**Slide 47 — What We Didn't Cover**
Title: Enterprise Production Checklist
Content: Two columns — "We Did" vs "Enterprise Also Needs":

We Did:
- Docker containerization
- Unit testing (pytest)
- Linting (ruff)
- CI/CD (GitHub Actions)
- Security scanning (Snyk, Trivy)
- Environment strategy
- Multi-cloud deployment
- LLM observability (LangSmith)

Enterprise Also Needs:
- Kubernetes orchestration
- Infrastructure as Code (Terraform)
- API authentication (OAuth2, JWT)
- Rate limiting and throttling
- Database migrations (Alembic)
- Load testing (Locust, k6)
- Compliance (SOC2, HIPAA, GDPR)
- Disaster recovery and backup
- Cost optimization and FinOps
- On-call rotation and incident management
- Feature flags (LaunchDarkly)
- A/B testing for LLM prompts
- Data privacy and PII handling
- Model versioning and registry
- Prompt versioning and management

**Slide 48 — Kubernetes: When You Outgrow Serverless**
Title: Serverless vs Kubernetes
Content:
| | Serverless (Cloud Run / App Runner) | Kubernetes (GKE / EKS / AKS) |
|--|--------------------------------------|-------------------------------|
| Setup | 5 minutes | Hours to days |
| Cost when idle | $0 | Cluster always running |
| Scaling | Automatic | Configurable (HPA) |
| Networking | Managed | Full control |
| GPU workloads | Limited | Full support |
| Multi-service | Basic | Service mesh (Istio) |
| Learning curve | Low | Steep |
Move to Kubernetes when you need: GPU inference, service mesh, custom networking, or 10+ microservices.

**Slide 49 — AI-Specific Production Concerns**
Title: What Makes AI Apps Different
Content:
- Prompt versioning: Track and version control your system prompts
- Model drift: Monitor answer quality over time
- Token budgets: Set per-user and per-org limits
- PII handling: Scrub personal data before sending to LLMs
- Fallback models: If GPT-4 is down, fall back to GPT-3.5
- Response caching: Cache common queries to reduce cost
- Guardrails: Content filtering, safety checks on LLM output
- Evaluation: Automated scoring of answer quality (relevance, faithfulness)
- RAG evaluation: Measure retrieval precision and recall

---

### CLOSING SLIDE (Slide 50)

**Slide 50 — Summary**
Title: What We Built Today
Content: Final pipeline diagram showing the complete flow:
```
Developer writes code
  → git push
    → GitHub Actions
      → Lint (ruff) ✓
      → Test (pytest) ✓
      → Security (Snyk + Trivy) ✓
      → Build Docker image ✓
      → Push to registry ✓
      → Deploy to Cloud ✓
        → GCP (Dev)
        → Azure (Staging)
        → AWS (Prod)
      → LangSmith traces everything ✓
    → App is live, monitored, and secure
```

**Footer**: "If it's not automated, it's not reliable."

**Bottom**: Repository: github.com/fnusatvik07/rag-cicd

---

## PROMPT END

---

## Recommended AI Presentation Tools

| Tool | Best For | URL |
|------|----------|-----|
| Gamma.app | Best AI slide generator, paste this prompt directly | https://gamma.app |
| Beautiful.ai | Professional templates with AI assist | https://beautiful.ai |
| Canva AI | Good visuals, needs more manual work | https://canva.com |
| Google Slides + Gemini | Free, decent AI features | https://slides.google.com |
| Tome | AI-first presentations | https://tome.app |

For best results with this prompt, use **Gamma.app** — paste the entire prompt above and it will generate all 50 slides with proper formatting.
