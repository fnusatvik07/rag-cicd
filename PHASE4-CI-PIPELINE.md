# Phase 4 - CI Pipeline (GitHub Actions)

## What is CI (Continuous Integration)?

CI means automatically validating your code every time someone pushes. Instead of relying on developers to remember to run tests and lint before pushing, the CI system does it automatically on a server.

If the code is bad, CI blocks it. If the code is good, CI gives it a green checkmark.

## What is GitHub Actions?

GitHub Actions is GitHub's built-in CI/CD platform. When you push code, GitHub spins up a fresh virtual machine (called a "runner"), runs your pipeline steps, and reports pass/fail.

Key concepts:
- **Workflow**: A YAML file in `.github/workflows/` that defines what to run
- **Trigger**: What starts the workflow (push, pull request, schedule, manual)
- **Job**: A group of steps that run on one runner (VM)
- **Step**: A single command or action
- **Runner**: A fresh Ubuntu/macOS/Windows VM that GitHub provides for free

## What was added

### `.github/workflows/ci.yml`

A single workflow file that runs 6 steps on every push and pull request.

## The Pipeline - Step by Step

```
git push
  |
  v
GitHub detects push, spins up a fresh Ubuntu VM
  |
  v
Step 1: Checkout code -----> Pull repo code onto the runner
  |
  v
Step 2: Setup Python ------> Install Python 3.13 on the runner
  |
  v
Step 3: Install deps ------> pip install uv, then uv pip install ".[test]" and ruff
  |
  v
Step 4: Lint (ruff) -------> GATE: ruff check .
  |                           Fail? -> Pipeline stops, red X on commit
  v
Step 5: Test (pytest) -----> GATE: pytest tests/ -v
  |                           Fail? -> Pipeline stops, red X on commit
  v
Step 6: Build Docker ------> GATE: docker build -t rag-classic:test .
  |                           Fail? -> Pipeline stops, red X on commit
  v
All passed -> Green checkmark on commit
```

## What each step does and why

### Step 1: Checkout code
```yaml
- uses: actions/checkout@v4
```
The runner starts as a blank Ubuntu VM with nothing on it. This step clones our repo onto the runner so the subsequent steps have code to work with. Without this, there's nothing to lint, test, or build.

### Step 2: Setup Python
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.13"
```
Installs Python 3.13 on the runner. The runner has a system Python but we need the exact version our app uses. Version mismatch = bugs that work locally but fail in production.

### Step 3: Install dependencies
```yaml
- run: |
    pip install uv
    uv venv .venv
    . .venv/bin/activate
    uv pip install ".[test]"
    uv pip install ruff
```
Same as what we do locally. Installs all app dependencies plus test tools (pytest, httpx) and linter (ruff). We use `uv` because it's faster than pip (~4x), which matters when this runs on every push.

### Step 4: Lint with ruff (QUALITY GATE)
```yaml
- run: |
    . .venv/bin/activate
    ruff check .
```
Runs the linter we configured in Phase 3. Catches unused imports, wrong syntax, style issues. If any file fails, the pipeline stops here. No point running tests on code that has obvious problems.

### Step 5: Run tests (QUALITY GATE)
```yaml
- run: |
    . .venv/bin/activate
    pytest tests/ -v
```
Runs all 17 unit tests from Phase 2. These tests don't need API keys - they test pure logic (chunking, context building, API validation). If any test fails, the pipeline stops. Broken logic must never reach production.

### Step 6: Build Docker image (QUALITY GATE)
```yaml
- run: docker build -t rag-classic:test .
```
Builds the Docker image from Phase 1's Dockerfile. This catches:
- Missing files that COPY references
- Broken dependency installation
- Syntax errors in Dockerfile

**Where does this Docker image go?** Nowhere yet. It's built on the runner to verify it works, then discarded when the job ends. The runner VM is temporary - it gets destroyed after the job finishes. In Phase 7 (Deploy), we'll push the image to a container registry (like Google Artifact Registry) so it can be deployed to Cloud Run.

## Where does the Docker image go?

Right now: **nowhere**. Here's the journey across phases:

```
Phase 4 (now):   docker build -> image exists on runner -> runner dies -> image gone
Phase 7 (later): docker build -> docker push to registry -> deploy from registry
```

| Phase | Build? | Push to registry? | Deploy? |
|-------|--------|-------------------|---------|
| Phase 4 (CI) | Yes | No | No |
| Phase 7 (CD) | Yes | Yes (Artifact Registry) | Yes (Cloud Run) |

The purpose of building in CI is to catch Dockerfile errors early. If the build breaks, we know before attempting to deploy.

## How to verify it works

1. Push this branch to GitHub:
```bash
git push rag-cicd phase/4-ci-pipeline
```

2. Go to GitHub repo -> Actions tab

3. You should see the "CI" workflow running with all 6 steps

4. To test a failure: break a lint rule or test, push, watch it fail with a red X

## Triggers explained

```yaml
on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]
```

- **push to develop/main**: Someone merged code. Validate it.
- **pull_request to develop/main**: Someone wants to merge code. Validate it BEFORE merging.

PRs show the CI result directly on the PR page. Reviewers can see if code passes before approving.

## Key Takeaways

1. **CI runs automatically** - no one needs to remember to run tests
2. **Fresh environment every time** - no "works on my machine" issues
3. **Quality gates stop bad code** - lint fails -> pipeline stops -> no deploy
4. **Docker build in CI** - catches Dockerfile errors before deployment
5. **Image is not pushed yet** - that's CD (Continuous Deployment) in Phase 7
6. **Free for public repos** - GitHub gives 2000 minutes/month for private repos
