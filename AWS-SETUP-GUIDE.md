# AWS App Runner Setup Guide - Complete Walkthrough

This guide covers everything needed to deploy the RAG app to AWS App Runner via GitHub Actions.

## Prerequisites

- An AWS account (fully activated — can take up to 24 hours after signup)
- AWS CLI installed (`brew install awscli` on Mac)
- A GitHub repo with the Dockerfile and deploy workflow

## Step 1: Create an AWS Account

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Enter email, password, account name
4. Choose "Personal" account type
5. Enter billing info (free tier covers this)
6. Verify phone number
7. Select "Basic support - Free" plan
8. Wait for account activation (can take up to 24 hours)

## Step 2: Install and Configure AWS CLI

```bash
# Install on Mac
brew install awscli

# Verify
aws --version
```

## Step 3: Create IAM User for GitHub Actions

1. Go to https://console.aws.amazon.com/iam/home#/users
2. Click "Create user"
3. User name: `github-deploy`
4. Click "Next"
5. Select "Attach policies directly"
6. Search and check these policies:
   - `AmazonEC2ContainerRegistryFullAccess` — push Docker images to ECR
   - `AWSAppRunnerFullAccess` — create and manage App Runner services
   - `IAMFullAccess` — create roles needed by App Runner
7. Click "Next" -> "Create user"

### Create Access Key

8. Click on the user `github-deploy`
9. Go to "Security credentials" tab
10. Scroll to "Access keys" -> Click "Create access key"
11. Select "Third-party service" -> check confirmation -> "Next" -> "Create access key"
12. Copy both values:
    - Access key ID (e.g., `AKIA...`)
    - Secret access key (keep this safe!)

## Step 4: Configure AWS CLI Locally

```bash
aws configure
```

Enter:
- AWS Access Key ID: `AKIA...` (from Step 3)
- Secret Access Key: (from Step 3)
- Default region name: `us-east-1`
- Default output format: `json`

## Step 5: Create ECR Repository

ECR (Elastic Container Registry) stores Docker images on AWS.

```bash
aws ecr create-repository --repository-name rag-classic --region us-east-1
```

Output will include:
```json
{
  "repository": {
    "repositoryUri": "123456789.dkr.ecr.us-east-1.amazonaws.com/rag-classic",
    "registryId": "123456789"
  }
}
```

Note your **registryId** (12-digit account ID).

## Step 6: Add GitHub Secrets

Go to: `https://github.com/<your-username>/<your-repo>/settings/environments`

### Create "production" environment:
1. Click "New environment" -> name it `production` -> "Configure"
2. Optional: Add yourself as "Required reviewer" (prod deploys need approval)
3. Under "Environment secrets", add:

| Secret Name | Value | Where to get it |
|-------------|-------|-----------------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | Step 3: IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | (secret key) | Step 3: IAM user secret key |
| `PINECONE_API_KEY` | Your Pinecone key | https://app.pinecone.io |
| `OPENAI_API_KEY` | Your OpenAI key | https://platform.openai.com/api-keys |
| `LANGSMITH_API_KEY` | Your LangSmith key | https://smith.langchain.com |

## Step 7: Deploy

Push to the `main` branch:

```bash
git checkout main
git push origin main
```

The workflow does everything automatically:
1. Lint + Test (CI gate)
2. Login to ECR
3. Build and push Docker image
4. Create IAM role for App Runner (first time)
5. Create/Update App Runner service
6. Print the live URL

## Step 8: Verify

```bash
# Get the URL from workflow output or AWS console
URL=https://xxxxx.us-east-1.awsapprunner.com

# Health check
curl $URL/health

# Swagger docs
open $URL/docs

# Ask a question
curl -X POST $URL/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in Q4 2024?"}'
```

## How to See the App in AWS Console

### View App Runner Service
1. Go to https://console.aws.amazon.com/apprunner
2. Click on `rag-classic-prod`
3. You'll see:
   - **Service URL**: Click to open the live app
   - **Status**: Running / Deploying / Failed
   - **Metrics tab**: Request count, latency, HTTP errors
   - **Logs tab**: Application logs (stdout/stderr)
   - **Configuration tab**: CPU, memory, env vars, health check

### View ECR Images
1. Go to https://console.aws.amazon.com/ecr
2. Click on `rag-classic` repository
3. See all pushed image tags (each commit SHA)

### View Deployment History
1. On the App Runner service page
2. Click "Activity" tab
3. Shows every deployment with status and timestamp

## App Runner vs Cloud Run vs Container Apps

| Feature | AWS App Runner | GCP Cloud Run | Azure Container Apps |
|---------|---------------|---------------|---------------------|
| Pricing | Pay per compute | Pay per request | Pay per compute |
| Scale to zero | Yes | Yes | Yes |
| Min cost | ~$5/month | $0 | $0 |
| Setup complexity | Low | Low | Medium |
| Health checks | Built-in | Built-in | Built-in |
| Custom domains | Yes | Yes | Yes |
| Region used | us-east-1 | us-central1 | eastus2 |

All three use the exact same Docker image.

## Troubleshooting

### "SubscriptionRequiredException"
- AWS account isn't fully activated yet. Wait up to 24 hours after signup.
- Visit https://console.aws.amazon.com/apprunner to trigger activation.

### "AccessDenied" errors
- Make sure IAM user has all 3 policies: ECR, AppRunner, IAM
- Check that access key ID and secret are correct in GitHub Secrets

### "ImageNotFoundException"
- Make sure ECR repository exists: `aws ecr describe-repositories`
- Check that the Docker push step succeeded before the deploy step

### Container keeps crashing
- Check App Runner logs: Console -> your service -> Logs tab
- Most common: missing env vars (API keys not set)

## Cleanup

To avoid charges after the class:

```bash
# Delete App Runner service
aws apprunner delete-service \
  --service-arn $(aws apprunner list-services \
    --query "ServiceSummaryList[?ServiceName=='rag-classic-prod'].ServiceArn | [0]" \
    --output text)

# Delete ECR repository and all images
aws ecr delete-repository --repository-name rag-classic --force

# Delete IAM role
aws iam detach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
aws iam delete-role --role-name AppRunnerECRAccessRole

# Delete IAM user (optional)
aws iam delete-access-key --user-name github-deploy --access-key-id AKIA...
aws iam detach-user-policy --user-name github-deploy --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
aws iam detach-user-policy --user-name github-deploy --policy-arn arn:aws:iam::aws:policy/AWSAppRunnerFullAccess
aws iam detach-user-policy --user-name github-deploy --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
aws iam delete-user --user-name github-deploy
```
