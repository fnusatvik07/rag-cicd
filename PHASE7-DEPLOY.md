# Phase 7 - Deployment (CD to Cloud Run)

## What is CD (Continuous Deployment)?

CD means automatically deploying code to a live environment after it passes all quality gates. Combined with CI from Phase 4:

```
CI (Phases 1-5)                           CD (Phase 7)
Lint -> Test -> Security -> Docker Build -> Push to Registry -> Deploy to Cloud Run
                                            |                    |
                                            WHERE the image      WHERE the app
                                            is stored            runs
```

## What is Google Cloud Run?

Cloud Run is a serverless container platform. You give it a Docker image, it runs it and gives you a URL. Key features:

- **Serverless**: No servers to manage, no patching, no scaling config
- **Scale to zero**: When no one is using the app, it scales down to 0 instances (no cost)
- **Auto-scale**: When traffic spikes, it spins up more instances automatically
- **Pay per request**: Only pay for the time your code is actually handling requests
- **Any Docker image**: If it runs in Docker, it runs on Cloud Run

## What is Artifact Registry?

Artifact Registry is Google's container image storage. Think of it as "GitHub for Docker images".

```
Phase 4: docker build -> image on runner -> runner dies -> image GONE
Phase 7: docker build -> docker push to Artifact Registry -> image STORED PERMANENTLY
                                                              |
                                                              Cloud Run pulls from here
```

Without a registry, every deploy would need to rebuild the image. With a registry, the image is built once and pulled anywhere.

## What was added

### `.github/workflows/deploy.yml`

The full CD pipeline with 2 jobs and 6 deploy steps.

## The Full Pipeline

```
git push to develop
  |
  v
Job 1: CI (must pass first)
  |-- Lint (ruff)
  |-- Test (pytest)
  |
  v (only if CI passes)
Job 2: Deploy
  |
  |-- Step 1: Authenticate to Google Cloud
  |            (using service account key from GitHub Secrets)
  |
  |-- Step 2: Configure Docker for Artifact Registry
  |            (so docker push sends to Google, not Docker Hub)
  |
  |-- Step 3: Build Docker image
  |            (tagged with commit SHA for traceability)
  |
  |-- Step 4: Push image to Artifact Registry
  |            (image now stored permanently in the cloud)
  |
  |-- Step 5: Deploy to Cloud Run
  |            (Cloud Run pulls image and starts serving traffic)
  |            (API keys injected as env vars, never in the image)
  |
  |-- Step 6: Print the live URL
               https://rag-classic-xxxxx.a.run.app
```

## Step-by-step explained

### Step 1: Authenticate to Google Cloud
```yaml
- uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}
```
The GitHub runner needs permission to push images and deploy. A GCP service account key (JSON) stored in GitHub Secrets gives it this access. The runner authenticates as this service account.

### Step 2: Configure Docker for Artifact Registry
```yaml
- run: gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
```
By default, `docker push` sends images to Docker Hub. This command reconfigures Docker to send images to Google's Artifact Registry instead.

### Step 3: Build Docker image
```yaml
- run: docker build -t $IMAGE:$GITHUB_SHA -t $IMAGE:latest .
```
Two tags:
- `$GITHUB_SHA` (e.g., `a1b2c3d`): The exact commit hash. You can always trace which code is running.
- `latest`: Convenience tag. Always points to the most recent build.

### Step 4: Push to Artifact Registry
```yaml
- run: |
    docker push $IMAGE:$GITHUB_SHA
    docker push $IMAGE:latest
```
Uploads both tagged images to Artifact Registry. Now they're stored permanently and can be pulled by Cloud Run or any authorized user.

### Step 5: Deploy to Cloud Run
```yaml
- run: |
    gcloud run deploy $SERVICE_NAME \
      --image $IMAGE:$GITHUB_SHA \
      --region $GCP_REGION \
      --platform managed \
      --allow-unauthenticated \
      --set-env-vars "PINECONE_API_KEY=${{ secrets.PINECONE_API_KEY }},OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" \
      --memory 512Mi \
      --cpu 1 \
      --min-instances 0 \
      --max-instances 3 \
      --timeout 60
```

| Flag | What it does |
|------|-------------|
| `--image` | Which Docker image to run (from Artifact Registry) |
| `--region` | Which data center (us-central1 = Iowa) |
| `--platform managed` | Fully managed by Google (no Kubernetes) |
| `--allow-unauthenticated` | Public endpoint (no auth required to hit /health) |
| `--set-env-vars` | Inject API keys from GitHub Secrets into the container |
| `--memory 512Mi` | Max RAM per instance |
| `--cpu 1` | 1 CPU per instance |
| `--min-instances 0` | Scale to zero when idle (saves money) |
| `--max-instances 3` | Max 3 instances during traffic spikes |
| `--timeout 60` | Max 60 seconds per request |

### Step 6: Show URL
```yaml
- run: |
    URL=$(gcloud run services describe $SERVICE_NAME --region $GCP_REGION --format 'value(status.url)')
    echo "Deployed to: $URL"
```
Prints the public URL where the app is now live.

## Other clouds - same pattern, different commands

| Step | GCP | AWS | Azure |
|------|-----|-----|-------|
| Registry | Artifact Registry | ECR (Elastic Container Registry) | ACR (Azure Container Registry) |
| Compute | Cloud Run | ECS Fargate / App Runner | Container Apps |
| Auth | Service Account Key | IAM Role + OIDC | Service Principal |
| Push | `gcloud auth configure-docker` | `aws ecr get-login-password` | `az acr login` |
| Deploy | `gcloud run deploy` | `aws ecs update-service` | `az containerapp update` |

The Docker image is the SAME on all clouds. Only the deployment commands change. This is the power of containers.

## GitHub Secrets required

These must be set in: GitHub Repo -> Settings -> Secrets and variables -> Actions

| Secret | What it is | Where to get it |
|--------|-----------|-----------------|
| `GCP_SA_KEY` | GCP service account JSON key | GCP Console -> IAM -> Service Accounts |
| `PINECONE_API_KEY` | Pinecone API key | Pinecone Console -> API Keys |
| `OPENAI_API_KEY` | OpenAI API key | OpenAI Platform -> API Keys |

## Verifying the deployment

After the pipeline runs:

```bash
# Health check
curl https://rag-classic-xxxxx.a.run.app/health

# Swagger docs (open in browser)
open https://rag-classic-xxxxx.a.run.app/docs

# Ask a question
curl -X POST https://rag-classic-xxxxx.a.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in Q4 2024?"}'
```

## Key Takeaways

1. **CI must pass before CD** - `needs: ci` ensures broken code never deploys
2. **Artifact Registry stores images** - the answer to "where does the Docker image go?"
3. **Commit SHA tagging** - always know exactly which code is running in production
4. **Secrets via env vars** - API keys go from GitHub Secrets -> Cloud Run, never in code or images
5. **Scale to zero** - `min-instances 0` means you pay nothing when no one is using the app
6. **Same image everywhere** - the Docker image is identical across GCP, AWS, and Azure
7. **One push = full deploy** - push to develop, sit back, watch it go live
