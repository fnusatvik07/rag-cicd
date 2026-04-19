# Phase 5 - Security Scanning

## Why security scanning in CI/CD?

Your app doesn't just run your code - it runs hundreds of third-party packages. Each package is maintained by someone else and can have security vulnerabilities. One vulnerable dependency in production can lead to:
- Data breaches (API keys leaked, user data exposed)
- Remote code execution (attacker runs code on your server)
- Denial of service (attacker crashes your app)

Security scanning catches these BEFORE they reach production.

## Types of Security Scanning

| Type | What it scans | Tool | When to use |
|------|--------------|------|-------------|
| **SCA** (Software Composition Analysis) | Third-party dependencies | Snyk, Dependabot | Every build |
| **SAST** (Static Application Security Testing) | Your source code | SonarQube, Semgrep | Every build |
| **Container Scanning** | Docker image OS packages | Trivy, Snyk Container | Every Docker build |
| **DAST** (Dynamic Application Security Testing) | Running application | OWASP ZAP, Burp Suite | Staging/Pre-prod |

In this phase we add **SCA** (Snyk) and **Container Scanning** (Trivy).

## What was added

### `.github/workflows/security.yml`

Two parallel security jobs that run on every push and PR.

## The Pipeline

```
git push
  |
  +---> Job 1: Snyk Dependency Scan
  |       |
  |       v
  |     Install deps -> Generate requirements.txt -> Snyk scans for CVEs
  |       |
  |       v
  |     Report: "fastapi 0.115.0 has CVE-2024-XXXX (HIGH)"
  |
  +---> Job 2: Docker Image Scan (runs in parallel)
          |
          v
        Build Docker image -> Trivy scans image layers
          |
          v
        Report: "libssl 3.0.2 has CVE-2023-XXXX (CRITICAL)"
```

Both jobs run in parallel (independent of each other).

## Job 1: Snyk Dependency Scan

### What is Snyk?
Snyk is a security platform that maintains a database of known vulnerabilities in open-source packages. When we give it our `requirements.txt`, it checks every package and version against this database.

### How it works
```yaml
- name: Install dependencies
  run: |
    uv pip install .
    uv pip freeze > requirements.txt    # List all packages with exact versions
```
First we generate `requirements.txt` so Snyk knows exactly which packages and versions we use.

```yaml
- name: Run Snyk security scan
  uses: snyk/actions/python-3.10@master
  continue-on-error: true
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    args: --severity-threshold=high --file=requirements.txt
```
- `SNYK_TOKEN`: API key stored in GitHub Secrets (never in code)
- `--severity-threshold=high`: Only fail on HIGH or CRITICAL severity
- `continue-on-error: true`: For demo purposes, report but don't block the build

### Severity levels
| Level | Meaning | Action |
|-------|---------|--------|
| Low | Minor issue, hard to exploit | Monitor |
| Medium | Possible exploit with specific conditions | Plan to fix |
| High | Exploitable vulnerability | Fix before deploy |
| Critical | Actively exploited in the wild | Fix immediately |

## Job 2: Docker Image Scan (Trivy)

### What is Trivy?
Trivy is a free, open-source vulnerability scanner. It scans Docker images for:
- OS package vulnerabilities (apt/apk packages in the base image)
- Python package vulnerabilities (same as Snyk but also catches OS-level issues)
- Misconfigurations

### How it works
```yaml
- name: Build Docker image
  run: docker build -t rag-classic:scan .

- name: Scan image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: rag-classic:scan
    format: table
    severity: HIGH,CRITICAL
    exit-code: 0
```
- Builds the image first, then scans every layer
- `severity: HIGH,CRITICAL`: Only show serious issues
- `exit-code: 0`: Report but don't fail (set to `1` in production to block deploys)

### Why scan the Docker image too?
Our `python:3.13-slim` base image contains OS packages (openssl, libc, etc.) that can have their own vulnerabilities. Snyk only catches Python packages. Trivy catches both.

## What is SonarQube/SonarCloud? (Conceptual)

SonarQube scans your SOURCE CODE (not dependencies) for:
- **Code smells**: Overly complex functions, duplicated code
- **Bugs**: Null pointer risks, resource leaks
- **Security hotspots**: Hardcoded passwords, SQL injection patterns
- **Test coverage**: What percentage of code is covered by tests

SonarCloud (cloud version) is free for public repos. It adds a dashboard showing:
```
Quality Gate: PASSED
  Bugs: 0
  Vulnerabilities: 0
  Code Smells: 3
  Coverage: 72%
  Duplications: 1.2%
```

We don't set it up hands-on (takes 15+ minutes to configure), but it's important to know it exists.

## OWASP Top 10 (Know the list)

The 10 most common web application security risks:

| # | Risk | Example |
|---|------|---------|
| 1 | Broken Access Control | User accesses admin endpoints |
| 2 | Cryptographic Failures | Passwords stored in plain text |
| 3 | Injection | SQL injection, command injection |
| 4 | Insecure Design | No rate limiting on login |
| 5 | Security Misconfiguration | Debug mode on in production |
| 6 | Vulnerable Components | Using packages with known CVEs |
| 7 | Auth Failures | Weak passwords, no MFA |
| 8 | Data Integrity Failures | No verification of updates |
| 9 | Logging Failures | No audit trail for actions |
| 10 | SSRF | Server makes requests to internal services |

Our security scanning addresses #6 (Vulnerable Components) directly.

## Setup Required

For Snyk to work, you need:
1. Create a free account at https://snyk.io
2. Get your API token from Snyk dashboard -> Settings -> API Token
3. Add it as a GitHub Secret: Repo -> Settings -> Secrets -> `SNYK_TOKEN`

Trivy needs no setup - it's fully open source and runs without tokens.

## Key Takeaways

1. **Your code is only as secure as your dependencies** - scan them automatically
2. **Two layers of scanning** - Python packages (Snyk) + Docker OS packages (Trivy)
3. **Severity matters** - don't block builds on low-severity issues, focus on HIGH/CRITICAL
4. **Shift left** - catch vulnerabilities in CI, not after deployment
5. **SonarQube for code quality** - scans your code for bugs, smells, and coverage
6. **OWASP Top 10** - the standard list of web security risks every developer should know
7. **Free tools exist** - Snyk (free tier), Trivy (open source), SonarCloud (free for public repos)
