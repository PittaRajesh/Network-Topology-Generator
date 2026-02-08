# CI/CD Pipeline Documentation

## Overview

The Networking Automation Engine implements a comprehensive, production-grade CI/CD pipeline using GitHub Actions. This pipeline ensures code quality, security, and reliable automated deployments.

## Architecture

```
Code Push/PR
    ↓
Lint & Quality Checks (parallel)
    ↓
Unit Tests (with databases)
    ↓
Security Scanning (SAST, container scan, dependencies)
    ↓
Docker Build & Push
    ↓
Integration Tests
    ↓
Deployment (manual approval)
```

## Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)

**Trigger Events:**
- Push to `main`, `develop`, `release/**` branches
- Pull requests to `main`, `develop`
- Nightly schedule at 02:00 UTC
- Changes to `app/`, `requirements.txt`, `Dockerfile`, `tests/`, `.github/workflows/`

**Stages:**

#### Stage 1: Lint & Code Quality (5-10 min)
Runs in parallel with other stages. Validates code formatting and style.

**Tools:**
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Style guide enforcement
- `mypy` - Static type checking
- `bandit` - Security issue detection

**Outputs:**
- Bandit JSON report (if vulnerabilities found)

**Example Output:**
```
✓ Code formatting OK (black)
✓ Import sorting OK (isort)
✓ Linting OK (flake8)
✓ Type checking completed (mypy)
✓ Security check completed (bandit)
```

#### Stage 2: Unit Tests (10-15 min)
Executes comprehensive test suite with PostgreSQL and Redis services.

**Services:**
- PostgreSQL 15 (test_db, test_user:test_password)
- Redis 7 (local instance)

**Coverage:**
- Line coverage reporting
- HTML report generation
- Codecov integration

**Example Command:**
```bash
pytest tests/ -v --cov=app --cov-report=xml --cov-report=html
```

**Outputs:**
- Test results
- Coverage report (XML and HTML)
- Artifact: `test-results/`

#### Stage 3: Security Scanning (8-12 min)
Parallel execution of multiple security tools.

**Tools:**
- **Trivy** - Vulnerability database scanning (FS and container)
- **OWASP Dependency Check** - Known vulnerability detection
- **Bandit** - Python security linter

**Outputs:**
- SARIF reports for GitHub Security tab
- Vulnerability summaries

#### Stage 4: Docker Build & Push (15-25 min)
Builds multi-stage Docker image and pushes to GitHub Container Registry.

**Features:**
- Layer caching for faster builds
- Semantic versioning with tags
- Metadata extraction from git refs

**Image Tags:**
```
ghcr.io/owner/repo:develop
ghcr.io/owner/repo:main
ghcr.io/owner/repo:v1.0.0
ghcr.io/owner/repo:main-abc123def
ghcr.io/owner/repo:latest (on main)
```

**Only runs on:**
- Pushed commits (not PRs)

#### Stage 5: Integration Tests (10-15 min)
Full stack integration testing with running services.

**Tests:**
- Service health checks
- API endpoint validation
- Topology generation workflow
- Configuration generation workflow

**Only runs on:**
- `main` branch after successful build

**Example Tests:**
```bash
# Test topology generation endpoint
curl -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d '{"name":"test","num_routers":3,"num_switches":1}'

# Test configuration generation
curl -X POST http://localhost:8000/api/v1/configuration/generate \
  -H "Content-Type: application/json" \
  -d '{...topology...}'
```

#### Stage 6: Deployment (Manual Approval)
Requires manual approval before proceeding.

**Environment:** Production
**Approval:** Required from repository maintainers
**Status:** Updates deployment tracking

#### Stage 7: Notifications
Workflow summary and Slack notifications on failure.

### 2. Code Quality Workflow (`code-quality.yml`)

**Trigger Events:**
- Push to `main`, `develop`
- Pull requests
- Nightly schedule at 03:00 UTC

**Tools:**

#### CodeQL Analysis
- Language: Python
- Queries: security-and-quality
- Database: GitHub CodeQL DB
- Output: SARIF reports in Security tab

#### SonarCloud Analysis
- Project key: `networking-automation-engine`
- Metrics: complexity, duplication, coverage
- PR decoration: Automatic comments on PRs
- Quality gate: Configurable thresholds

**Reports Location:**
- GitHub: Security → Code scanning
- SonarCloud: Dashboard at sonarcloud.io

### 3. Container Build Workflow (`container-build.yml`)

**Trigger Events:**
- Push to `main`, `develop`
- Push of tags (v*)
- Manual workflow dispatch

**Tasks:**

1. **Build Docker Image**
   - Multi-stage build with layer caching
   - Context: Entire repository
   - Cache strategy: GHA cache and registry cache

2. **Generate SBOM** (Software Bill of Materials)
   - Tool: Anchore SBOM action
   - Format: SPDX JSON
   - Artifact: `sbom.spdx.json`
   - Use case: Supply chain security, license compliance

3. **Container Scanning**
   - Tool: Trivy
   - Scanning: Published image
   - Format: SARIF
   - Severity: All levels reported

### 4. Release Workflow (`release.yml`)

**Trigger Events:**
- Git tags matching `v*` (e.g., `v1.0.0`, `v1.0.0-beta`)
- Manual workflow dispatch

**Tasks:**

1. **Create GitHub Release**
   - Title: "Release v1.0.0"
   - Changelog generation
   - Asset uploads

2. **Publish to DockerHub** (optional)
   - Tags: Latest and version-specific
   - Registry: Docker Hub (requires secrets)
   - Push: Both `latest` and `v1.0.0` tags

3. **Publish Documentation**
   - Artifact: Release documentation bundle
   - Includes: README, DEPLOYMENT.md, RELEASE_NOTES.md
   - Location: Release artifacts

## Secrets & Configuration

### Required GitHub Secrets

| Secret | Purpose | Example |
|--------|---------|---------|
| `GITHUB_TOKEN` | Auto-provided, authenticate with GHCR | N/A (automatic) |
| `DOCKERHUB_USERNAME` | Docker Hub authentication | `myusername` |
| `DOCKERHUB_TOKEN` | Docker Hub token | Personal access token |
| `SONAR_TOKEN` | SonarCloud authentication | From sonarcloud.io |
| `SLACK_WEBHOOK_URL` | Slack notifications | `https://hooks.slack.com/...` |

### Environment Variables

**GitHub Actions Secrets:**
```bash
# In .github/workflows/*.yml
secrets:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
```

**GitHub Variables (public):**
```bash
# In .github/variables
REGISTRY: ghcr.io
IMAGE_NAME: ${{ github.repository }}
```

## Setting Up Secrets

### 1. GHCR (GitHub Container Registry)
Already configured - uses `GITHUB_TOKEN` automatically.

### 2. Docker Hub
1. Create personal access token at hub.docker.com/settings/security
2. Go to repository Settings → Secrets and variables → Actions
3. Create secrets:
   ```
   DOCKERHUB_USERNAME = <your-username>
   DOCKERHUB_TOKEN = <your-token>
   ```

### 3. SonarCloud
1. Sign up at sonarcloud.io
2. Get token from sonarcloud.io/account/security
3. Create secret:
   ```
   SONAR_TOKEN = <your-token>
   ```
4. Create `sonar-project.properties`:
   ```properties
   sonar.projectKey=networking-automation-engine
   sonar.organization=<your-organization>
   ```

### 4. Slack Notifications
1. Create Slack webhook: api.slack.com/apps → Incoming Webhooks
2. Create secret:
   ```
   SLACK_WEBHOOK_URL = <your-webhook-url>
   ```

## Pipeline Execution

### Local Testing

Test workflows locally with `act`:

```bash
# Install act
brew install act  # macOS
# or download from https://github.com/nektos/act

# List available workflows
act --list

# Run a specific workflow
act -j test

# Run with secrets
act -s GITHUB_TOKEN=ghp_xxx secrets --list

# Run with job logs
act -j lint --verbose
```

### Triggering Workflows

**Via Git:**
```bash
# Automatic trigger - push to main
git push origin main

# Create a release
git tag v1.0.0
git push origin v1.0.0

# Trigger nightly build (wait for scheduled time)
# Or use workflow_dispatch for manual trigger
```

**Via GitHub UI:**
1. Go to repository → Actions
2. Select workflow
3. Click "Run workflow" → "Run workflow"

### Monitoring Workflow Execution

**GitHub UI:**
1. Repository → Actions tab
2. Click workflow run name
3. View job logs

**Command Line:**
```bash
# Using GitHub CLI
gh run list
gh run view <run-id> --log
gh run logs <run-id>
```

## Deployment Procedures

### Automatic Deployment

**Trigger:**
- Successful build on `main` branch
- All checks pass
- Manual approval in deployment environment

**Process:**
1. Docker image pushed to GHCR
2. Integration tests execute
3. Manual approval prompt
4. Deployment tracked in GitHub Deployments

### Manual Deployment

Deploy versioned release:

```bash
# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Using containerlab
./scripts/deploy-containerlab.sh --ci
```

### Pre-deployment Checks

```bash
# Validate configuration
docker-compose config

# Check image security
trivy image ghcr.io/owner/repo:latest

# Verify health
curl http://localhost:8000/api/v1/info
```

## Troubleshooting

### Common Issues

**1. Workflow Failed at "Lint" Stage**
```
❌ Code not formatted with black
Solution:
  black app/ tests/
  git add .
  git commit -m "Format code"
  git push
```

**2. Test Coverage Below Threshold**
```
❌ Coverage dropped to 75% (threshold: 80%)
Solution:
  # Add missing tests
  pytest tests/ --cov=app --cov-report=term-missing
  # Review uncovered lines and add tests
```

**3. Docker Build Timeout**
```
❌ Build timed out after 30 minutes
Solution:
  # Check for large files
  git lfs install
  
  # Optimize Dockerfile layers
  # Combine RUN commands
  # Move frequently changing code to end
```

**4. Security Scan Vulnerabilities**
```
❌ Critical vulnerability found
Solution:
  # Check specific CVE
  trivy image ghcr.io/owner/repo:latest
  
  # Update dependency
  pip install --upgrade vulnerable-package
  
  # Update requirements.txt and push
```

### Debug Mode

Enable debug logging in workflows:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      ACTIONS_STEP_DEBUG: true  # Enable step debug output
```

View debug output:
1. Go to workflow run
2. Click "Enable debug logging"
3. Re-run workflow

## Performance Optimization

### Cache Strategies

**Pip Dependencies:**
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    cache: 'pip'
```

**Docker Layers:**
```yaml
cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
```

### Parallel Job Execution

Jobs run in parallel by default:
- `lint` - 5 minutes
- `test` - 10 minutes  
- `security` - 8 minutes
- All run simultaneously
- `build` waits for all three

Total time: ~15 minutes (not 23)

## Best Practices

### 1. Commit Hygiene
- Small, focused commits
- Clear commit messages referencing issues
- Run local checks before pushing:
  ```bash
  ./scripts/ci-cd-utils.sh all
  ```

### 2. Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `release/*` - Release branches
- `hotfix/*` - Emergency fixes

### 3. Pull Request Process
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit
3. Push: `git push origin feature/my-feature`
4. Create PR with description
5. Wait for CI to pass
6. Request review
7. Merge after approval

### 4. Version Management
- Semantic versioning: `MAJOR.MINOR.PATCH`
- Tag releases: `git tag v1.2.3`
- Create GitHub Release for each tag

### 5. Documentation
- Update README.md with user-facing changes
- Update CHANGELOG.md before releases
- Document new environment variables
- Update deployment procedures if needed

## Advanced Configuration

### Custom Environments

Add staging environment:

```yaml
# In workflow
environment:
  name: staging
  url: https://staging.example.com
```

### Conditional Steps

Run step only on main branch:

```yaml
- name: Deploy to production
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: ./deploy.sh
```

### Matrix Strategy

Test multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
steps:
  - uses: actions/setup-python@v4
    with:
      python-version: ${{ matrix.python-version }}
```

## Monitoring & Alerts

### GitHub Notifications
- Subscribe to workflow failures
- Repository → Settings → Notifications

### Email Alerts
- GitHub sends notifications for failures
- Configure in Settings → Notifications

### Slack Integration
Configured in workflow:
```yaml
- name: Slack notification
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Metrics & Reports

**Codecov Dashboard:**
- Coverage trends over time
- Per-file coverage breakdown
- Pull request impact analysis

**SonarCloud Dashboard:**
- Code quality metrics
- Technical debt
- Security hotspots

**GitHub Actions:**
- Usage statistics
- Runner capacity
- Billing information

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Best Practices](https://docker.com/blog/docker-best-practices/)
- [act - Local GitHub Actions Runner](https://github.com/nektos/act)

## Support

For pipeline issues or improvements:
1. Check recent workflow runs
2. Review error logs
3. Test locally with `act`
4. Open an issue with workflow logs
5. Update this documentation
