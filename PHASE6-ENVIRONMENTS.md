# Phase 6 - Environments

## What are environments?

Environments are separate copies of your application, each serving a different purpose in the software delivery lifecycle. Code flows through environments before reaching real users.

```
Developer Laptop  ->  Dev  ->  QA  ->  Staging  ->  Production
     |                 |        |        |              |
  You write code    Auto-     QA team   Final         Real
  and test locally  deploy    tests     check         users
                    on push   here      (mirror       here
                                        of prod)
```

## Why multiple environments?

Without environments:
```
Developer writes code -> Pushes to production -> Bug hits users -> Panic
```

With environments:
```
Developer writes code -> Dev (auto) -> QA (manual test) -> Staging (final check) -> Production
                         Bug caught    Bug caught          Bug caught               Users safe
                         early         by QA team          before release
```

Each environment is a safety net. The further right a bug travels, the more expensive it is to fix.

## The Four Environments

### 1. Dev (Development)
- **Purpose**: First integration point. Code from multiple developers comes together here.
- **Deploys**: Automatically on every push to `develop` branch
- **Who uses it**: Developers
- **Data**: Fake/test data, test API keys
- **Stability**: Can break. That's OK.
```
Branch: develop -> auto-deploy to Dev
```

### 2. QA (Quality Assurance)
- **Purpose**: QA team tests features end-to-end
- **Deploys**: Manually triggered or on release candidate branches
- **Who uses it**: QA engineers, product managers
- **Data**: Realistic test data (not production data)
- **Stability**: Should be stable enough to test
```
Branch: release/* -> deploy to QA
```

### 3. Staging
- **Purpose**: Mirror of production. Final validation before going live.
- **Deploys**: After QA approval
- **Who uses it**: QA team for final sign-off, engineers for smoke tests
- **Data**: Production-like data (anonymized)
- **Stability**: Must be stable. If it works here, it works in prod.
```
Rule: Staging must match production exactly (same infra, same config, same scale)
```

### 4. Production
- **Purpose**: Real users, real money, real consequences
- **Deploys**: After staging sign-off, with manual approval
- **Who uses it**: Real users
- **Data**: Real data
- **Stability**: Must be rock solid
```
Branch: main -> deploy to Production (requires approval)
```

## What changes between environments?

The CODE is the same Docker image everywhere. Only the CONFIGURATION changes:

| Setting | Dev | QA | Staging | Prod |
|---------|-----|------|---------|------|
| `PINECONE_INDEX_NAME` | `rag-classic-dev` | `rag-classic-qa` | `rag-classic-staging` | `rag-classic` |
| `PINECONE_API_KEY` | dev key | qa key | staging key | prod key |
| `OPENAI_API_KEY` | dev key | qa key | staging key | prod key |
| `OPENAI_MODEL` | `gpt-4o-mini` | `gpt-4o-mini` | `gpt-4o` | `gpt-4o` |
| Cloud Run instances | 0-1 | 0-1 | 1-2 | 2-10 |
| Domain | dev.app.com | qa.app.com | staging.app.com | app.com |

**Key principle**: Same image, different config. Never rebuild code per environment.

## Branch Strategy

```
feature/add-auth ──> develop ──> main
                       |           |
                       v           v
                    Dev/QA     Staging/Prod
```

- **feature/* branches**: Where developers write code
- **develop**: Integration branch. Merging here triggers Dev deploy.
- **main**: Production branch. Merging here triggers Staging/Prod deploy.
- **Pull Requests**: feature -> develop (code review required)
- **Release**: develop -> main (QA approval + staging sign-off required)

## How this maps to GitHub Actions

```yaml
# Deploy to Dev - automatic on every push to develop
deploy-dev:
  if: github.ref == 'refs/heads/develop'
  environment: development

# Deploy to Prod - only on main, requires manual approval
deploy-prod:
  if: github.ref == 'refs/heads/main'
  environment: production    # GitHub Environment with approval rules
```

### GitHub Environments feature
GitHub has a built-in "Environments" feature (Repo -> Settings -> Environments) that lets you:
- Set environment-specific secrets (different API keys per env)
- Require manual approval before deploying (for staging/prod)
- Add wait timers (e.g., wait 5 minutes before deploying to prod)
- Restrict which branches can deploy to which environments

## What was added

### `.env.example`

A template showing what environment variables exist and how they change per environment. This file IS committed (unlike `.env` which is gitignored). New developers copy this file to `.env` and fill in their values.

```
# Dev:     rag-classic-dev
# QA:      rag-classic-qa
# Staging: rag-classic-staging
# Prod:    rag-classic
PINECONE_INDEX_NAME=rag-classic
```

## Secrets Management (Conceptual)

Never store secrets in code. Here's where secrets live in each context:

| Context | Where secrets live |
|---------|-------------------|
| Local development | `.env` file (gitignored) |
| GitHub Actions | GitHub Secrets (Repo -> Settings -> Secrets) |
| Cloud Run | Environment variables set during deployment |
| Enterprise | HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager |

The flow:
```
Developer adds secret to GitHub Secrets
  -> GitHub Actions reads it: ${{ secrets.PINECONE_API_KEY }}
  -> Passes it to Cloud Run: --set-env-vars "PINECONE_API_KEY=xxx"
  -> App reads it: os.getenv("PINECONE_API_KEY")
```

Secret never appears in code, logs, or Docker images.

## Rollback Strategy (Conceptual)

What if a production deploy breaks?

| Strategy | How it works | Downtime |
|----------|-------------|----------|
| **Revert commit** | Git revert + re-deploy | Minutes |
| **Cloud Run revisions** | Route traffic back to previous revision | Seconds |
| **Blue/Green** | Two identical environments, swap traffic | Zero |
| **Canary** | Send 5% traffic to new version, watch for errors | Zero |

Cloud Run makes rollback easy: every deploy creates a new "revision". You can route 100% traffic back to the previous revision with one click.

## Key Takeaways

1. **Same image, different config** - never rebuild code per environment
2. **Dev is for breaking, Prod is for stability** - bugs should be caught early
3. **Secrets live outside code** - .env locally, GitHub Secrets in CI, env vars in cloud
4. **Branch strategy matters** - feature -> develop -> main maps to Dev -> QA -> Prod
5. **Manual approval for prod** - GitHub Environments enforce this
6. **Rollback plan** - always know how to go back to the previous version
