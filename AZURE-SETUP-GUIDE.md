# Azure Container Apps Setup Guide - Complete Walkthrough

This guide covers everything needed to deploy the RAG app to Azure Container Apps via GitHub Actions.

## Prerequisites

- A Microsoft/Azure account
- Azure CLI installed locally (`brew install azure-cli` on Mac)
- A GitHub repo with the Dockerfile and deploy workflow

## Step 1: Create an Azure Account

1. Go to https://azure.microsoft.com/free
2. Click "Start free"
3. Sign in with Microsoft account
4. Enter billing info (Azure gives $200 free credit for 30 days)
5. Once done, you land on the Azure Portal: https://portal.azure.com

## Step 2: Login to Azure CLI

```bash
az login
```

This opens a browser window to authenticate. After login, verify:

```bash
# Check your subscription ID (you'll need this later)
az account show --query id -o tsv
# Example output: YOUR_SUBSCRIPTION_ID
```

## Step 3: Create a Resource Group

A resource group is a container that holds all related Azure resources.

**In Portal:**
1. Search "Resource groups" in the top search bar
2. Click "+ Create"
3. Resource group name: `rag-classic-rg`
4. Region: `East US 2`
5. Click "Review + create" -> "Create"

**Or via CLI:**
```bash
az group create --name rag-classic-rg --location eastus2
```

## Step 4: Create Azure Container Registry (ACR)

ACR is where Docker images are stored (like GCP Artifact Registry).

**In Portal:**
1. Search "Container registries" in the search bar
2. Click "+ Create"
3. Fill in:
   - Resource group: `rag-classic-rg`
   - Registry name: `ragclassicacr` (lowercase, globally unique, no dashes)
   - Location: `East US 2`
   - SKU: `Basic`
4. Click "Review + create" -> "Create"

**Or via CLI:**
```bash
az acr create \
  --resource-group rag-classic-rg \
  --name ragclassicacr \
  --sku Basic \
  --admin-enabled true
```

### Get ACR Credentials

**In Portal:**
1. Go to your container registry (ragclassicacr)
2. Click "Access keys" in the left sidebar
3. Toggle "Admin user" to Enabled
4. Note down:
   - Login server: `ragclassicacr.azurecr.io`
   - Username: `ragclassicacr`
   - Password: (copy the password value)

**Or via CLI:**
```bash
# Get login server
az acr show --name ragclassicacr --query loginServer -o tsv
# Output: ragclassicacr.azurecr.io

# Get credentials
az acr credential show --name ragclassicacr
# Output shows username and two passwords
```

## Step 5: Create a Service Principal

A service principal is a "robot identity" that GitHub Actions uses to authenticate with Azure.

```bash
# Replace <SUBSCRIPTION_ID> with your actual subscription ID
az ad sp create-for-rbac \
  --name "github-deploy-staging" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rag-classic-rg
```

**Example with real subscription ID:**
```bash
az ad sp create-for-rbac \
  --name "github-deploy-staging" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/rag-classic-rg
```

**Output (save this!):**
```json
{
  "appId": "YOUR_APP_ID",
  "displayName": "github-deploy-staging",
  "password": "YOUR_SERVICE_PRINCIPAL_PASSWORD",
  "tenant": "YOUR_TENANT_ID"
}
```

## Step 6: Add GitHub Secrets

Go to: `https://github.com/<your-username>/<your-repo>/settings/environments`

### Create "staging" environment:
1. Click "New environment" -> name it `staging` -> "Configure"
2. Under "Environment secrets", click "Add secret" for each:

| Secret Name | Value | Where to get it |
|-------------|-------|-----------------|
| `AZURE_CREDENTIALS` | JSON (see below) | Built from Step 5 output |
| `ACR_LOGIN_SERVER` | `ragclassicacr.azurecr.io` | Step 4: ACR Access keys |
| `ACR_USERNAME` | `ragclassicacr` | Step 4: ACR Access keys |
| `ACR_PASSWORD` | (the password value) | Step 4: ACR Access keys |
| `PINECONE_API_KEY` | Your Pinecone API key | https://app.pinecone.io |
| `OPENAI_API_KEY` | Your OpenAI API key | https://platform.openai.com/api-keys |
| `LANGSMITH_API_KEY` | Your LangSmith API key | https://smith.langchain.com |

### AZURE_CREDENTIALS format

Build this JSON from the service principal output (Step 5):

```json
{
  "clientId": "<appId from Step 5>",
  "clientSecret": "<password from Step 5>",
  "subscriptionId": "<your subscription ID from Step 2>",
  "tenantId": "<tenant from Step 5>"
}
```

**Example:**
```json
{
  "clientId": "YOUR_APP_ID",
  "clientSecret": "YOUR_SERVICE_PRINCIPAL_PASSWORD",
  "subscriptionId": "YOUR_SUBSCRIPTION_ID",
  "tenantId": "YOUR_TENANT_ID"
}
```

## Step 7: Deploy

Push to the `staging` branch:

```bash
git checkout staging
git push origin staging
```

The workflow does everything automatically:
1. Lint + Test (CI gate)
2. Login to Azure
3. Build Docker image
4. Push image to ACR
5. Create Container Apps environment (first time)
6. Create/Update the Container App
7. Print the live URL

## Step 8: Verify

```bash
# Get the URL from workflow output or Azure portal
URL=https://rag-classic-stage.xxxxx.eastus2.azurecontainerapps.io

# Health check
curl $URL/health

# Swagger docs
open $URL/docs

# Ask a question
curl -X POST $URL/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in Q4 2024?"}'
```

## How to See the App in Azure Portal

### View the Container App
1. Go to https://portal.azure.com
2. Search "Container Apps" in the search bar
3. Click on `rag-classic-stage`
4. You'll see:
   - **Overview**: Status, URL, resource usage
   - **Application URL**: Click to open the live app
   - **Revisions**: Every deployment creates a new revision (for rollback)

### View Logs
1. On the Container App page, click **"Log stream"** in the left sidebar
2. This shows real-time logs (like `docker logs`)
3. Or click **"Logs"** for historical log queries

### View Metrics
1. On the Container App page, click **"Metrics"** in the left sidebar
2. Select metrics like:
   - Request count
   - Response latency
   - CPU usage
   - Memory usage

### View Container Registry Images
1. Search "Container registries" in the search bar
2. Click `ragclassicacr`
3. Click **"Repositories"** in the left sidebar
4. Click `rag-classic-stage` to see all pushed image tags

### View Environment Variables
1. On the Container App page, click **"Containers"** in the left sidebar
2. You'll see the environment variables configured (values are hidden)

## How the Workflow Works

```
git push to staging
  |
  v
GitHub Actions triggers "Deploy: Azure (Staging)"
  |
  ├── CI: lint + test
  |
  ├── az login (using AZURE_CREDENTIALS from GitHub Secrets)
  |
  ├── docker login to ACR (ragclassicacr.azurecr.io)
  |
  ├── docker build + docker push to ACR
  |
  ├── az containerapp env create (first time only)
  |
  ├── Does app exist?
  |   ├── No:  az containerapp create (with env vars, ports, scaling)
  |   └── Yes: az containerapp update (just update the image + env vars)
  |
  └── Print deployed URL
```

## GCP vs Azure Comparison

| Feature | GCP (Cloud Run) | Azure (Container Apps) |
|---------|----------------|----------------------|
| Registry | Artifact Registry | ACR |
| Compute | Cloud Run | Container Apps |
| Auth | Service Account JSON | Service Principal JSON |
| Min cost | $0 (scale to zero) | $0 (scale to zero) |
| Deploy command | `gcloud run deploy` | `az containerapp create/update` |
| Logs | Cloud Logging | Log stream |
| Revisions | Built-in | Built-in |
| Region used | us-central1 | eastus2 |

Both use the exact same Docker image. Only the deployment commands differ.

## Troubleshooting

### "The containerapp does not exist"
- This means the app hasn't been created yet. The workflow handles this by checking first (Step 5 check-app) and running `create` for first deploy.

### "Unauthorized" or "Permission denied"
- Verify AZURE_CREDENTIALS JSON has correct clientId, clientSecret, subscriptionId, tenantId
- Make sure the service principal has "contributor" role on the resource group

### "Image not found"
- Verify ACR_LOGIN_SERVER, ACR_USERNAME, ACR_PASSWORD are correct
- Check that admin user is enabled on the ACR

### Container keeps crashing
- Check Log stream in Azure portal for Python errors
- Most common: missing env vars (API keys not set)
- Increase memory if you see OOM errors

## Cleanup

To avoid charges after the class:

```bash
# Delete everything in the resource group (Container App + Environment + ACR)
az group delete --name rag-classic-rg --yes --no-wait

# Or delete individually:
az containerapp delete --name rag-classic-stage --resource-group rag-classic-rg --yes
az containerapp env delete --name rag-classic-env --resource-group rag-classic-rg --yes
az acr delete --name ragclassicacr --yes

# Delete the service principal
az ad sp delete --id YOUR_APP_ID
```
