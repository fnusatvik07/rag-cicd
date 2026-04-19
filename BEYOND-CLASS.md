# Beyond the Class - Production Topics

What we built in this class is a solid foundation. Here's what comes next when you take this to real production.

## Cloud Run vs Kubernetes - What We Deployed

What we used: **Cloud Run** — a serverless container platform.

```
Cloud Run (what we did)
  - Give it a Docker image, it runs it
  - Auto-scales, scale to zero
  - Pay per request
  - No servers to manage
  - Good for: APIs, microservices, small-medium traffic

Kubernetes (the next level)
  - Container orchestration platform
  - You manage clusters of machines
  - Full control over networking, scaling, storage
  - Good for: large-scale, complex multi-service architectures
```

### Cloud Run is NOT Kubernetes

Cloud Run runs on Google's internal infrastructure. It's simpler than Kubernetes:

| Feature | Cloud Run | Kubernetes (GKE/EKS/AKS) |
|---------|-----------|--------------------------|
| Setup time | 5 minutes | Hours to days |
| Scaling | Automatic, scale to zero | Manual config or HPA |
| Networking | Managed, one URL | Ingress controllers, service mesh |
| Cost when idle | $0 (scale to zero) | Cluster always running (~$70+/month) |
| Max complexity | Low-medium | Unlimited |
| Learning curve | Low | Steep |
| When to use | Single service, moderate traffic | Multi-service, high traffic, custom networking |

### When to Move to Kubernetes

You outgrow Cloud Run when you need:
- Multiple services talking to each other (service mesh)
- Custom networking rules (VPC, private endpoints)
- GPU workloads (ML model serving)
- Persistent storage (databases running in containers)
- Fine-grained scaling rules (scale on custom metrics, not just requests)

### Kubernetes Deployment - What It Looks Like

Instead of `gcloud run deploy`, you write YAML manifests:

```yaml
# deployment.yaml - tells K8s what to run
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-classic
spec:
  replicas: 3                    # run 3 instances
  selector:
    matchLabels:
      app: rag-classic
  template:
    spec:
      containers:
        - name: rag-classic
          image: us-central1-docker.pkg.dev/project/repo/rag-classic:latest
          ports:
            - containerPort: 8080
          env:
            - name: PINECONE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: pinecone-key
          resources:
            limits:
              memory: "2Gi"
              cpu: "2"
---
# service.yaml - exposes it to the internet
apiVersion: v1
kind: Service
metadata:
  name: rag-classic
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: rag-classic
---
# hpa.yaml - auto-scaling rules
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-classic
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-classic
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

The Docker image is THE SAME. Only the deployment method changes.

### Kubernetes Services

| Cloud | Kubernetes Service | Managed? |
|-------|-------------------|----------|
| GCP | GKE (Google Kubernetes Engine) | Yes |
| AWS | EKS (Elastic Kubernetes Service) | Yes |
| Azure | AKS (Azure Kubernetes Service) | Yes |
| Self-hosted | k3s, kubeadm | No |

## Rate Limiting

Prevent abuse by limiting how many requests a client can make.

### Option 1: Application-Level (FastAPI middleware)

```python
# Using slowapi library
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")      # max 10 requests per minute per IP
def chat_endpoint(req: ChatRequest):
    ...
```

### Option 2: API Gateway (Cloud-level)

| Cloud | Service | How |
|-------|---------|-----|
| GCP | Cloud Armor / API Gateway | Rate limit rules per IP/region |
| AWS | API Gateway + WAF | Throttling settings per endpoint |
| Azure | API Management | Rate limit policies |

### Option 3: Reverse Proxy (Nginx/Traefik)

```nginx
# Nginx rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /chat {
    limit_req zone=api burst=20;
    proxy_pass http://rag-classic:8080;
}
```

**Recommendation**: Start with application-level (slowapi), add cloud-level when you need DDoS protection.

## Traffic Management

### Blue/Green Deployment
```
v1 (Blue) ← 100% traffic     v2 (Green) ← 0% traffic
                    ↓ deploy + test
v1 (Blue) ← 0% traffic       v2 (Green) ← 100% traffic
                    ↓ if something breaks
v1 (Blue) ← 100% traffic     v2 (Green) ← 0% (rollback instant)
```

Cloud Run does this with **revisions** — every deploy creates a new revision, you can split traffic:
```bash
gcloud run services update-traffic rag-classic \
  --to-revisions=rag-classic-00005=90,rag-classic-00006=10
```
This sends 90% to old version, 10% to new (canary deployment).

### Canary Deployment
```
v1 ← 95% traffic
v2 ← 5% traffic    ← watch for errors
         ↓ looks good after 30 min
v1 ← 0%
v2 ← 100%          ← full rollout
```

## Authentication & Security

### API Key Authentication
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/chat")
def chat(req: ChatRequest, api_key: str = Security(api_key_header)):
    if api_key != os.getenv("APP_API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    ...
```

### Cloud-Level Auth
- Cloud Run: `--no-allow-unauthenticated` + IAM roles
- API Gateway: OAuth2, JWT tokens
- Firebase Auth: For user-facing apps

## Observability & Telemetry

### LangSmith (LLM-specific, recommended for this app)
Zero code changes — just add env vars:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=rag-classic
```

What it shows:
- Every LLM call: prompt, response, tokens used, cost
- Full chain trace: ingestion -> retrieval -> rerank -> generate
- Latency breakdown per step
- Error tracking

### Infrastructure Monitoring

| What to monitor | Tool | Free tier |
|----------------|------|-----------|
| Request latency, error rate | Cloud Run built-in metrics | Yes |
| Logs | Cloud Logging (GCP) | 50 GB/month |
| Custom dashboards | Grafana Cloud | Yes (limited) |
| Full APM | Datadog, New Relic | Trial only |
| Uptime checks | Google Cloud Monitoring | Yes |

### Key Metrics to Watch in Production

| Metric | Why it matters | Alert threshold |
|--------|---------------|-----------------|
| Request latency (p95) | User experience | > 5 seconds |
| Error rate (5xx) | App is broken | > 1% |
| Token usage | Cost control | > daily budget |
| Cold start time | First request delay | > 10 seconds |
| Memory usage | OOM crashes | > 80% |
| Retrieval relevance | RAG quality | Score < 0.5 |

## Infrastructure as Code (IaC)

Instead of clicking through GCP console, define infrastructure in code:

### Terraform Example
```hcl
# main.tf - defines the Cloud Run service
resource "google_cloud_run_service" "rag" {
  name     = "rag-classic"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "us-central1-docker.pkg.dev/project/repo/rag-classic:latest"
        resources {
          limits = {
            memory = "2Gi"
            cpu    = "2"
          }
        }
        env {
          name = "PINECONE_API_KEY"
          value_from {
            secret_key_ref {
              name = "pinecone-key"
              key  = "latest"
            }
          }
        }
      }
    }
  }
}
```

Benefits:
- Infrastructure is version controlled (Git)
- Reproducible across environments
- Reviewable in PRs
- Can spin up/tear down entire environments in one command

## Database Migrations in CI/CD

If your app had a database (PostgreSQL, etc.), schema changes need their own pipeline:

```
Code change + Migration file
  -> CI runs tests
  -> CD applies migration FIRST
  -> Then deploys new code
  -> If migration fails, stop everything
```

Tools: Alembic (Python/SQLAlchemy), Flyway (Java), golang-migrate

## Summary: Production Readiness Checklist

| Category | What | Status in our class |
|----------|------|-------------------|
| Containerization | Docker | Done |
| CI Pipeline | Lint + Test + Build | Done |
| Security Scanning | Snyk + Trivy | Done |
| CD Pipeline | Auto-deploy to Cloud Run | Done |
| Environments | Dev/QA/Staging/Prod strategy | Conceptual |
| Rate Limiting | API throttling | Not done |
| Authentication | API keys / OAuth | Not done |
| Telemetry | LangSmith / monitoring | Not done |
| IaC | Terraform | Not done |
| Kubernetes | Container orchestration | Not done |
| Traffic Management | Blue/Green, Canary | Not done |
| Database Migrations | Schema version control | Not applicable (no DB) |
