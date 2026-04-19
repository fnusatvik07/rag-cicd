# Deployment Setup Guide - GCP Cloud Run

This guide covers every step needed to deploy the RAG app to Google Cloud Run via GitHub Actions - from creating a GCP account to seeing the app live.

## Overview

What we're setting up:

```
GitHub Actions (CI/CD)
  |
  +--> Authenticates with GCP (using service account key)
  |
  +--> Pushes Docker image to Artifact Registry (image storage)
  |
  +--> Deploys to Cloud Run (serverless containers)
        |
        +--> Injects API keys as env vars (from GitHub Secrets)
        |
        +--> App is live at https://rag-classic-xxx.a.run.app
```

## Part 1: GCP Setup

### Step 1.1: Create a GCP Account

1. Go to https://cloud.google.com
2. Click "Get started for free"
3. Sign in with your Google account
4. Enter billing info
   - Google gives $300 free credit
   - Won't charge without your permission
5. You land on the GCP Console Dashboard

### Step 1.2: Create a Project

1. At the top of the console, click the project dropdown (next to "Google Cloud" logo)
2. Click "New Project"
3. Project name: `rag-pipeline` (or any name you prefer)
4. Click "Create"
5. Wait a few seconds, then select the project from the dropdown
6. Note your **Project ID** - it's shown below the project name
   - Example: `rag-pipeline-493809`
   - You'll need this in multiple places later

### Step 1.3: Enable Required APIs

Two APIs must be enabled before deployment works:

1. Go to https://console.cloud.google.com/apis/library
2. Make sure your project is selected in the top dropdown
3. Search for **"Cloud Run Admin API"**
   - Click on it
   - Click "Enable"
   - Wait for it to enable
4. Go back to the API library
5. Search for **"Artifact Registry API"**
   - Click on it
   - Click "Enable"

Without these APIs enabled, the deployment will fail with "API not enabled" errors.

### Step 1.4: Create Artifact Registry Repository

Artifact Registry is where Docker images are stored. Cloud Run pulls images from here.

1. Go to https://console.cloud.google.com/artifacts
2. Click "Create Repository"
3. Fill in:
   - **Name**: `rag-classic`
   - **Format**: Docker
   - **Mode**: Standard
   - **Location type**: Region
   - **Region**: `us-central1 (Iowa)`
4. Leave everything else as default:
   - Encryption: Google-managed encryption key
   - Immutable image tags: Disabled
   - Cleanup policies: empty
   - Vulnerability scanning: Disabled (we use Trivy in CI)
5. Click "Create"

### Step 1.5: Create a Service Account

A service account is a "robot identity" that GitHub Actions uses to authenticate with GCP. It's like creating a user specifically for automation.

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "+ Create Service Account" at the top
3. Fill in:
   - **Service account name**: `github-deploy`
   - **Service account ID**: auto-fills as `github-deploy`
   - **Description**: `GitHub Actions deploys to Cloud Run`
4. Click "Create and Continue"
5. Now add **3 roles** (click the role dropdown, search for each one):

| Role | Why It's Needed |
|------|----------------|
| `Artifact Registry Writer` | Push Docker images to Artifact Registry |
| `Cloud Run Admin` | Create and update Cloud Run services |
| `Service Account User` | Allow the service account to act as itself during deployment |

   - Click "Select a role" dropdown
   - Search "Artifact Registry Writer" -> select it
   - Click "+ Add Another Role"
   - Search "Cloud Run Admin" -> select it
   - Click "+ Add Another Role"
   - Search "Service Account User" -> select it
6. Click "Continue"
7. Click "Done"

### Step 1.6: Create a JSON Key for the Service Account

This JSON key is what GitHub Actions uses to prove it's the `github-deploy` service account.

1. On the Service Accounts page, you should see `github-deploy` listed
2. Click on `github-deploy@<your-project-id>.iam.gserviceaccount.com`
3. Go to the **"Keys"** tab at the top
4. Click "Add Key" -> "Create new key"
5. Select **JSON** format
6. Click "Create"
7. A `.json` file will download to your computer

**This file contains credentials. Keep it safe:**
- Never commit it to Git
- Never share it publicly
- Delete it from your computer after adding to GitHub Secrets

The JSON file looks something like:
```json
{
  "type": "service_account",
  "project_id": "rag-pipeline-493809",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "github-deploy@rag-pipeline-493809.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

## Part 2: GitHub Secrets Setup

GitHub Secrets are encrypted values that GitHub Actions can read during workflow execution. They never appear in logs.

### Step 2.1: Navigate to Secrets

Go to: `https://github.com/<your-username>/<your-repo>/settings/secrets/actions`

Or: Repository -> Settings -> Secrets and variables -> Actions

### Step 2.2: Add Repository Secrets

Click "New repository secret" for each:

#### Secret 1: `GCP_SA_KEY`
- **Name**: `GCP_SA_KEY`
- **Value**: Open the downloaded JSON file from Step 1.6, copy the ENTIRE contents (including the curly braces), paste it
- Click "Add secret"

#### Secret 2: `PINECONE_API_KEY`
- **Name**: `PINECONE_API_KEY`
- **Value**: Your Pinecone API key
- Where to find it: https://app.pinecone.io -> API Keys
- Click "Add secret"

#### Secret 3: `OPENAI_API_KEY`
- **Name**: `OPENAI_API_KEY`
- **Value**: Your OpenAI API key
- Where to find it: https://platform.openai.com/api-keys
- Click "Add secret"

#### Secret 4: `LANGSMITH_API_KEY` (optional, for telemetry)
- **Name**: `LANGSMITH_API_KEY`
- **Value**: Your LangSmith API key
- Where to find it: https://smith.langchain.com -> Settings -> API Keys
- Click "Add secret"

### Step 2.3: Verify Secrets

After adding all secrets, you should see:

```
Repository secrets
  GCP_SA_KEY          Updated just now
  LANGSMITH_API_KEY   Updated just now
  OPENAI_API_KEY      Updated just now
  PINECONE_API_KEY    Updated just now
```

You can't view the values after saving (they're encrypted). If you need to change one, click "Update" and paste the new value.

### Step 2.4: Environment-Specific Secrets (optional)

For different API keys per environment (dev/staging/prod):

1. Go to: Repository -> Settings -> Environments
2. Click "New environment" -> name it `dev` -> Configure
3. Under "Environment secrets", add the same secrets with environment-specific values
4. Repeat for `staging` and `production`

When the workflow uses `environment: dev`, it reads secrets from that environment instead of repository-level secrets.

## Part 3: Update the Workflow

### Step 3.1: Set Your Project ID

In `.github/workflows/deploy.yml`, update these values:

```yaml
env:
  GCP_PROJECT_ID: rag-pipeline-493809                    # YOUR project ID
  GCP_REGION: us-central1
  SERVICE_NAME: rag-classic
  IMAGE: us-central1-docker.pkg.dev/rag-pipeline-493809/rag-classic/rag-classic
  #      ^region            ^project-id        ^repo-name  ^image-name
```

Replace `rag-pipeline-493809` with your actual Project ID (from Step 1.2).

### Step 3.2: How Secrets Flow in the Workflow

```yaml
# GitHub Actions reads secrets and passes them to Cloud Run
- name: Deploy to Cloud Run
  run: |
    gcloud run deploy $SERVICE_NAME \
      --set-env-vars "PINECONE_API_KEY=${{ secrets.PINECONE_API_KEY }}" \
      ...
```

The flow:
```
GitHub Secrets (encrypted, you added them)
  |
  ${{ secrets.PINECONE_API_KEY }}    <- GitHub Actions reads the secret
  |
  --set-env-vars "PINECONE_API_KEY=pcsk_xxx..."    <- passed to Cloud Run
  |
  Cloud Run container starts with PINECONE_API_KEY as env var
  |
  app/config.py: os.getenv("PINECONE_API_KEY")    <- app reads it
```

At no point is the secret visible in logs, code, or the Docker image.

## Part 4: Deploy

### Step 4.1: Push to Trigger

```bash
git push origin develop
```

### Step 4.2: Watch the Pipeline

1. Go to https://github.com/<your-username>/<your-repo>/actions
2. Click on the "Deploy" workflow run
3. Watch it execute:
   - CI job: lint, test (must pass first)
   - Deploy job: authenticate, build, push, deploy
4. The last step prints the live URL

### Step 4.3: Verify the Deployment

```bash
# Get URL from workflow output or GCP Console
URL=https://rag-classic-xxxxx-uc.a.run.app

# Health check
curl $URL/health
# Expected: {"status":"ok"}

# Swagger docs (open in browser)
open $URL/docs

# Ask a question
curl -X POST $URL/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in Q4 2024?"}'
```

### Step 4.4: View in GCP Console

1. Go to https://console.cloud.google.com/run
2. Click on `rag-classic-dev` (or your service name)
3. You'll see:
   - **URL** at the top - the live endpoint
   - **Metrics** - request count, latency, error rate
   - **Revisions** - every deployment creates a revision (for rollback)
   - **Logs** - click "Logs" tab to see application logs

## Troubleshooting

### "Container failed to start and listen on port"
**Cause**: App crashes on startup, usually because API keys are missing.
**Fix**:
- Verify secrets are set: GitHub -> Settings -> Secrets -> check all 3 exist
- Check Cloud Run logs for the actual Python error
- Common: `PineconeConfigurationError: You haven't specified an API key`
- Make sure secret names match EXACTLY: `PINECONE_API_KEY` not `Pinecone_API_Key`

### "Permission denied" or "Forbidden"
**Cause**: Service account doesn't have the right roles.
**Fix**:
- Go to IAM -> Service Accounts -> github-deploy
- Verify it has all 3 roles: Artifact Registry Writer, Cloud Run Admin, Service Account User

### "API not enabled"
**Cause**: Cloud Run or Artifact Registry API not enabled.
**Fix**: Follow Step 1.3 again

### "Image not found"
**Cause**: Artifact Registry repository doesn't exist or region mismatch.
**Fix**:
- Verify repo exists: https://console.cloud.google.com/artifacts
- Check region in both repo (Step 1.4) and workflow (Step 3.1) match

### Build succeeds but deploy fails
**Cause**: Usually memory or startup timeout.
**Fix**: Increase memory and CPU in deploy.yml:
```yaml
--memory 2Gi \
--cpu 2 \
```

## Cleanup (After Class)

To avoid charges:

```bash
# Delete the Cloud Run service
gcloud run services delete rag-classic-dev --region us-central1 --quiet

# Delete all images in Artifact Registry
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/rag-classic/rag-classic --quiet

# Delete the Artifact Registry repo
gcloud artifacts repositories delete rag-classic --location us-central1 --quiet

# Or delete the entire project (removes everything)
gcloud projects delete YOUR_PROJECT_ID
```

## Cost Summary

| Resource | Free Tier | Our Usage |
|----------|-----------|-----------|
| Cloud Run | 2M requests/month, 360K vCPU-sec | Well within free tier |
| Artifact Registry | 500 MB storage | ~200 MB (1 image) |
| GCP Free Credit | $300 for 90 days | Barely touched |

With `--min-instances 0` (scale to zero), there is zero cost when no one is using the app.
