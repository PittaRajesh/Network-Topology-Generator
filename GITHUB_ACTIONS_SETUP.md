# GitHub Actions Configuration Guide

## Quick Setup

### 1. Configure Repository Secrets

All secrets must be added to your GitHub repository to enable full CI/CD functionality.

**Navigate to:**
```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

### 2. Required Secrets

#### GitHub Container Registry (GHCR)
**Status:** ✓ Auto-configured
- Uses `GITHUB_TOKEN` automatically
- No manual setup required

#### Docker Hub (Optional)
**If pushing to Docker Hub:**

1. Create Personal Access Token:
   - Visit: hub.docker.com/settings/security
   - Create token with read/write permissions
   - Copy token

2. Add to GitHub:
   - Secret name: `DOCKERHUB_USERNAME`
   - Secret value: Your Docker Hub username
   
   - Secret name: `DOCKERHUB_TOKEN`
   - Secret value: Your personal access token

**Verify in Workflow:**
```yaml
# workflow will use these secrets
uses: docker/login-action@v2
with:
  username: ${{ secrets.DOCKERHUB_USERNAME }}
  password: ${{ secrets.DOCKERHUB_TOKEN }}
```

#### SonarCloud (Optional)
**For code quality analysis:**

1. Sign up: sonarcloud.io (works with GitHub account)
2. Create organization
3. Generate token:
   - sonarcloud.io → Account → Security → Generate token
4. Add to GitHub:
   - Secret name: `SONAR_TOKEN`
   - Secret value: Your SonarCloud token

**Note:** Also create `sonar-project.properties` in repo root (already provided)

#### Slack Notifications (Optional)
**For failure alerts:**

1. Create Slack App:
   - Visit: api.slack.com/apps
   - Create New App → From scratch
   - App name: "GitHub Notifications"
   - Workspace: Your Slack workspace

2. Enable Incoming Webhooks:
   - Features → Incoming Webhooks → On
   - Add New Webhook to Workspace
   - Select notification channel
   - Copy Webhook URL

3. Add to GitHub:
   - Secret name: `SLACK_WEBHOOK_URL`
   - Secret value: Your webhook URL

### 3. Branch Protection Rules

Enforce CI checks before merge:

**Navigate to:**
```
Repository → Settings → Branches → Branch protection rules → New rule
```

**Configure:**
- Branch name pattern: `main`
- Required status checks:
  - ✓ Lint & Code Quality
  - ✓ Unit Tests
  - ✓ Security Scan
  - ✓ Build Docker Image
- Require code reviews: 1-2 approvals
- Dismiss stale reviews: ✓
- Include administrators: ✓

### 4. Environments

Set up deployment environments:

**Navigate to:**
```
Repository → Environments → New environment
```

**Production Environment:**
- Name: `production`
- Deployment branches: `main`
- Required reviewers: Select team leads
- Protection rules: Add secrets specific to production

**Staging Environment:**
- Name: `staging`
- Deployment branches: `develop`
- No approval needed (for testing)

### 5. Variables (Public Configuration)

**Navigate to:**
```
Repository → Settings → Secrets and variables → Variables
```

**Create Variables:**
```
REGISTRY = ghcr.io
IMAGE_NAME = owner/repo
```

Reference in workflows:
```yaml
env:
  REGISTRY: ${{ vars.REGISTRY }}
  IMAGE_NAME: ${{ vars.IMAGE_NAME }}
```

## Workflow Customization

### Change Build Schedule

Edit `.github/workflows/ci-cd.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Change to your preferred time
              ↑ ↑ ↑ ↑ ↑
              | | | | day of week (0=Sunday)
              | | | month
              | | day of month
              | hour (UTC)
              minute
```

**Common schedules:**
```
0 2 * * *     = 2:00 AM UTC daily
0 2 * * 1-5   = 2:00 AM UTC weekdays only
0 */4 * * *   = Every 4 hours
0 0 * * 0     = Sunday midnight
```

### Change Build Branches

Edit any workflow file:

```yaml
on:
  push:
    branches:
      - main        # Change branches here
      - develop
      - 'release/**'
```

### Add New Test Services

Edit ci-cd.yml test job:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    # ... existing config ...
  
  my-new-service:  # Add service
    image: my-service:latest
    ports:
      - 9000:9000
    options: >-
      --health-cmd "curl http://localhost:9000"
      --health-interval 10s
```

### Modify Deployment Approval

Edit ci-cd.yml deploy job:

```yaml
deploy:
  environment:
    name: production
    url: https://example.com
    # Add automatic deployment (if no manual approval needed):
    auto_merge: true  # Auto-merge deployment PRs
```

## Handling Workflow Failures

### 1. Re-run Failed Workflow

**GitHub UI:**
```
Actions → Select workflow run → Re-run jobs → Re-run failed jobs
```

**GitHub CLI:**
```bash
gh run rerun <run-id> --failed
```

### 2. Skip Workflow Execution

Add `[skip ci]` to commit message:

```bash
git commit -m "Update docs [skip ci]"
git push
```

### 3. Debug Failed Step

Enable debug logging:

1. Go to Failed Workflow Run
2. Click "Enable debug logging"
3. Re-run the workflow
4. Check logs for detailed output

**Or set in workflow:**
```yaml
env:
  ACTIONS_STEP_DEBUG: true
```

### 4. Test Locally Before Pushing

Use `act` to test workflows locally:

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Run workflow
act -j test

# Run with secrets
act -j build --secret GITHUB_TOKEN=ghp_xxxx
```

## Performance Tuning

### Speed Up Docker Builds

Use buildx with cache:

```yaml
- uses: docker/setup-buildx-action@v2
- uses: docker/build-push-action@v4
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

This caches layers in GitHub Actions cache, reducing build time from ~15 min to ~3 min on subsequent runs.

### Speed Up Python Tests

Use pip cache:

```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    cache: 'pip'
```

### Parallel Job Execution

Jobs already run in parallel. Total time:
- 3 checks (lint, test, security): 15-25 min
- All parallel: ~25 min total (not 45+ min)

To optimize further:
1. Split slow tests into multiple jobs
2. Use matrix strategy for different Python versions
3. Cache dependencies aggressively

## Troubleshooting Guide

### Issue: Workflow stuck on "Waiting for available runner"

**Solution:**
- Check GitHub Actions quota (Settings → Billing)
- Use `ubuntu-latest` instead of specific version
- Ubuntu latest has more available runners

### Issue: GHCR push fails with "401 Unauthorized"

**Solution:**
```yaml
- uses: docker/login-action@v2
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}  # Make sure this is auto-provided
```

### Issue: Tests pass locally but fail in GitHub Actions

**Solution:**
1. Check environment variables:
   ```bash
   # GitHub Actions provides different env vars than local
   echo $GITHUB_REF
   echo $GITHUB_SHA
   echo $RUNNER_OS
   ```

2. Run act locally:
   ```bash
   act -j test --env GITHUB_TOKEN=ghp_xxx
   ```

3. Check for OS-specific code:
   ```python
   import platform
   if platform.system() == "Windows":
      # Use Windows-specific code
   ```

### Issue: Deployment environment not found

**Solution:**
1. Create environment in Settings → Environments
2. Verify environment name matches workflow exactly:
   ```yaml
   environment:
     name: production  # Must match exactly
   ```

## Workflow Examples

### Example 1: Deploy to AWS

```yaml
deploy:
  runs-on: ubuntu-latest
  environment: production
  steps:
    - uses: actions/checkout@v3
    - uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    - run: aws s3 cp app.tar.gz s3://my-bucket/
```

### Example 2: Manual Workflow Dispatch

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production
```

### Example 3: Conditional Deployment

```yaml
deploy:
  if: |
    github.event_name == 'push' &&
    github.ref == 'refs/heads/main' &&
    contains(github.actor, 'admin')  # Only admins can deploy
  runs-on: ubuntu-latest
  steps:
    - run: ./deploy-to-production.sh
```

## Security Best Practices

### 1. Secrets Management
- ✓ Always use `${{ secrets.NAME }}`
- ✓ Never commit secrets to code
- ✓ Rotate secrets regularly (every 90 days)
- ✓ Audit secret usage in Settings → Security log

### 2. Access Control
- ✓ Use environment protection rules
- ✓ Require approvals for production
- ✓ Limit deployment actors
- ✓ Enable branch protection rules

### 3. Dependency Management
- ✓ Pin action versions: `uses: actions/checkout@v3` (not @main)
- ✓ Regularly update dependencies
- ✓ Use SBOM for supply chain security
- ✓ Scan images for vulnerabilities

### 4. Least Privilege
- ✓ Use fine-grained personal access tokens
- ✓ Scope secrets to specific repositories
- ✓ Review and remove unused secrets quarterly
- ✓ Use role-based access control

## References

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitHub Secrets Guide](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

## Next Steps

1. ✓ Add repository secrets (5 min)
2. ✓ Enable branch protection (2 min)
3. ✓ Configure environments (5 min)
4. ✓ Test workflow execution (10 min)
5. ✓ Monitor first workflow run (5 min)

**Total setup time:** ~25 minutes

---

**Questions?** Check the CICD.md documentation for detailed workflow information.
