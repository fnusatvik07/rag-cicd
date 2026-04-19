# GCP Cloud Run Setup Guide - Complete Walkthrough

This guide covers everything needed to deploy the RAG app to Google Cloud Run via GitHub Actions.

## Prerequisites

- A Google account
- A GitHub repo with the Dockerfile and deploy workflow
- API keys for Pinecone and OpenAI

## Step 1: Create a GCP Account

1. Go to https://cloud.google.com
2. Click "Get started for free"
3. Sign in with Google account
4. Enter billing info (Google gives $300 free credit, won't charge without permission)
5. You land on the GCP Console Dashboard

## Step 2: Create a Project

1. Click the project dropdown at the top (next to "Google Cloud" logo)
2. Click "New Project"
3. Project name: `rag-pipeline` (or any name)
4. Click "Create"
5. Select the project from the dropdown
6. Note your **Project ID** (e.g., `rag-pipeline-493809`) — you'll need this

## Step 3: Enable APIs

Two APIs must be enabled for Cloud Run deployment:

1. Go to https://console.cloud.google.com/apis/library
2. Make sure your project is selected in the top dropdown
3. Search for **"Cloud Run Admin API"** -> Click it -> Click **"Enable"**
4. Go back, search for **"Artifact Registry API"** -> Click it -> Click **"Enable"**

## Step 4: Create Artifact Registry Repository

This is where Docker images are stored in the cloud.

1. Go to https://console.cloud.google.com/artifacts
2. Click "Create Repository"
3. Fill in:
   - Name: `rag-classic`
   - Format: `Docker`
   - Mode: `Standard`
   - Location type: `Region`
   - Region: `us-central1 (Iowa)`
4. Leave everything else as default (Google-managed encryption, etc.)
5. Click "Create"

## Step 5: Create a Service Account

A service account is a "robot user" that GitHub Actions uses to authenticate with GCP.

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "+ Create Service Account"
3. Fill in:
   - Service account name: `github-deploy`
   - Description: `GitHub Actions deploys to Cloud Run`
4. Click "Create and Continue"
5. Add these 3 roles (click the role dropdown, search for each):
   - `Artifact Registry Writer` — permission to push Docker images
   - `Cloud Run Admin` — permission to deploy services
   - `Service Account User` — permission to act as itself during deploy
6. Click "Continue" -> then "Done"

## Step 6: Create a JSON Key

1. On the Service Accounts page, click on `github-deploy@<project-id>.iam.gserviceaccount.com`
2. Go to the "Keys" tab
3. Click "Add Key" -> "Create new key"
4. Select "JSON" -> Click "Create"
5. A `.json` file downloads — this is the service account credential

**IMPORTANT**: Keep this file safe. Never commit it to Git. Delete it after adding to GitHub Secrets.

## Step 7: Add GitHub Secrets

Go to: `https://github.com/<your-username>/<your-repo>/settings/secrets/actions/new`

Add these 3 secrets:

| Secret Name | Value | Where to get it |
|-------------|-------|-----------------|
| `GCP_SA_KEY` | Entire contents of the downloaded JSON file | Step 6 above |
| `PINECONE_API_KEY` | Your Pinecone API key | https://app.pinecone.io -> API Keys |
| `OPENAI_API_KEY` | Your OpenAI API key | https://platform.openai.com/api-keys |

## Step 8: Update the Workflow

In `.github/workflows/deploy.yml`, update these values to match your project:

```yaml
env:
  GCP_PROJECT_ID: your-project-id          # e.g., rag-pipeline-493809
  GCP_REGION: us-central1                   # or your preferred region
  SERVICE_NAME: rag-classic                 # your Cloud Run service name
  IMAGE: us-central1-docker.pkg.dev/your-project-id/rag-classic/rag-classic
```

## Step 9: Push and Deploy

```bash
git push origin develop
```

The workflow will:
1. Run lint + tests (CI gate)
2. Build Docker image
3. Push to Artifact Registry
4. Deploy to Cloud Run
5. Print the live URL

## Step 10: Verify

```bash
# Get the URL from Cloud Run console or workflow output
URL=https://rag-classic-xxxxx-uc.a.run.app

# Health check
curl $URL/health

# Swagger docs
open $URL/docs

# Ask a question
curl -X POST $URL/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in Q4 2024?"}'
```

## Troubleshooting

### "Container failed to start and listen on port"
- **Missing API keys**: Make sure `PINECONE_API_KEY` and `OPENAI_API_KEY` are in GitHub Secrets
- **Memory too low**: Use `--memory 2Gi` for heavy Python libraries
- **Check logs**: Go to Cloud Run console -> your service -> Logs tab

### "Permission denied" errors
- Make sure the service account has all 3 roles (Step 5)
- Make sure Artifact Registry API and Cloud Run API are enabled (Step 3)

### "Image not found"
- Make sure Artifact Registry repo exists (Step 4)
- Make sure region matches in both the repo and the workflow

## Cost

With the free tier and scale-to-zero (`--min-instances 0`):
- No traffic = no cost
- Free tier includes 2 million requests/month and 360,000 vCPU-seconds/month
- The $300 free credit covers a lot of experimentation

## Cleanup

To avoid any charges after the class:

```bash
# Delete the Cloud Run service
gcloud run services delete rag-classic --region us-central1

# Delete the Artifact Registry repo
gcloud artifacts repositories delete rag-classic --location us-central1

# Or delete the entire project
gcloud projects delete your-project-id
```
