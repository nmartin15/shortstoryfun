# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Short Story Pipeline project.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and provides:

- **Automated Testing**: Runs on every push and pull request
- **Code Coverage Reporting**: Tracks test coverage across Python and JavaScript code
- **Code Quality Checks**: Linting, formatting, and type checking
- **Security Scanning**: Dependency vulnerability scanning and code security analysis
- **Automated Deployment**: Deploys to multiple platforms on main branch merges

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**

#### Python Tests
- Runs on Python 3.9, 3.10, and 3.11
- Installs dependencies with pip caching
- Runs pytest with coverage reporting
- Generates JUnit XML test results
- Uploads coverage to Codecov
- Uploads test artifacts and HTML coverage reports

#### JavaScript Tests
- Runs on Node.js 18
- Installs npm dependencies with caching
- Runs Jest tests with coverage
- Uploads coverage to Codecov
- Uploads test artifacts

#### Code Quality Checks
- Checks code formatting with Black
- Validates import sorting with isort
- Runs flake8 for code quality
- All checks are non-blocking (continue-on-error: true)

#### Type Checking
- Runs mypy for type checking
- Non-blocking to allow gradual type annotation adoption

#### Coverage Summary
- Aggregates coverage from all test jobs
- Posts coverage summary as PR comment
- Sets minimum coverage thresholds (85% green, 70% orange)

### 2. Deployment Workflow (`.github/workflows/deploy.yml`)

**Triggers:**
- Push to `main` branch
- Tags starting with `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch with environment selection

**Jobs:**

#### Deploy to Heroku
- Deploys to Heroku using Heroku CLI
- Requires `HEROKU_API_KEY` and `HEROKU_APP_NAME` secrets

#### Deploy to Railway
- Deploys to Railway using Railway API
- Requires `RAILWAY_TOKEN` and `RAILWAY_SERVICE_ID` secrets

#### Deploy to Render
- Triggers Render deployment via API
- Requires `RENDER_SERVICE_ID` and `RENDER_DEPLOY_KEY` secrets

#### Docker Build and Push
- Builds Docker image using Docker Buildx
- Pushes to Docker Hub with tags: `latest` and commit SHA
- Requires `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
- Uses GitHub Actions cache for faster builds

#### Deployment Notification
- Creates deployment summary in GitHub Actions
- Shows status of all deployment jobs

### 3. Security Workflow (`.github/workflows/security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Weekly schedule (Sunday at midnight)

**Jobs:**

#### Dependency Vulnerability Scan
- Scans Python dependencies with Safety
- Scans npm dependencies with `npm audit`
- Non-blocking to allow review of vulnerabilities

#### Python Security Linting
- Runs Bandit security linter on Python code
- Generates JSON report
- Uploads report as artifact

### 4. CodeQL Analysis (`.github/workflows/codeql.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Weekly schedule (Sunday at midnight)

**Jobs:**

#### CodeQL Analysis
- Analyzes Python and JavaScript code for security vulnerabilities
- Uses GitHub's CodeQL engine
- Results appear in Security tab of repository

## Configuration Files

### pytest.ini

Centralized pytest configuration:
- Test discovery patterns
- Output options (verbose, short tracebacks)
- Test markers (slow, integration, unit, api, redis, llm)
- Timeout settings (300 seconds)
- Logging configuration
- Warning filters

### requirements-dev.txt

Development dependencies including:
- Testing tools (pytest, pytest-cov, pytest-xdist, pytest-mock)
- Code quality tools (flake8, black, isort, mypy)
- Type stubs for better type checking

Install with:
```bash
pip install -r requirements-dev.txt
```

### Dockerfile

Production-ready Docker image:
- Based on Python 3.9-slim
- Non-root user for security
- Health check endpoint
- Optimized layer caching

### .dockerignore

Excludes unnecessary files from Docker builds to reduce image size and improve build speed.

## Required GitHub Secrets

### For CI/CD:

| Secret | Description | Required For |
|--------|-------------|--------------|
| `GOOGLE_API_KEY` | Google Gemini API key (optional, uses test key if not set) | CI tests |
| `CODECOV_TOKEN` | Codecov token for coverage uploads (optional) | Coverage reporting |

### For Deployment:

| Secret | Description | Required For |
|--------|-------------|--------------|
| `HEROKU_API_KEY` | Heroku API key | Heroku deployment |
| `HEROKU_APP_NAME` | Heroku app name | Heroku deployment |
| `RAILWAY_TOKEN` | Railway API token | Railway deployment |
| `RAILWAY_SERVICE_ID` | Railway service ID | Railway deployment |
| `RENDER_SERVICE_ID` | Render service ID | Render deployment |
| `RENDER_DEPLOY_KEY` | Render deploy key | Render deployment |
| `DOCKER_USERNAME` | Docker Hub username | Docker builds |
| `DOCKER_PASSWORD` | Docker Hub password/token | Docker builds |

## Setting Up Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its corresponding value

## Coverage Reporting

### Codecov Integration

The pipeline automatically uploads coverage reports to Codecov:

1. **Sign up** at [codecov.io](https://codecov.io) with your GitHub account
2. **Add your repository** to Codecov
3. Coverage reports will appear automatically in PRs and the Codecov dashboard

### Coverage Thresholds

- **Green**: ≥85% coverage
- **Orange**: 70-84% coverage
- **Red**: <70% coverage

### Viewing Coverage Locally

```bash
# Run tests with coverage
pytest tests/ --cov=src/shortstory --cov-report=html

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Dependabot

Automated dependency updates are configured via `.github/dependabot.yml`:

- **Python dependencies**: Weekly updates on Mondays
- **GitHub Actions**: Weekly updates on Mondays
- **npm dependencies**: Weekly updates on Mondays

Dependabot will:
- Create pull requests for dependency updates
- Limit open PRs to prevent spam
- Add appropriate labels
- Request review from maintainers

## Best Practices

### For Developers

1. **Run tests locally before pushing:**
   ```bash
   pytest tests/ -v
   npm test
   ```

2. **Check code quality:**
   ```bash
   black --check src/ tests/
   isort --check-only src/ tests/
   flake8 src/ tests/
   ```

3. **Ensure tests pass before merging PRs:**
   - All CI checks must pass
   - Code review required
   - Coverage should not decrease significantly

4. **Use test markers for slow tests:**
   ```python
   @pytest.mark.slow
   def test_long_running_operation():
       # ...
   ```

### For Maintainers

1. **Monitor CI/CD pipeline health:**
   - Check GitHub Actions tab regularly
   - Review failed builds promptly
   - Address flaky tests

2. **Review security scans:**
   - Check Security tab for vulnerabilities
   - Update dependencies with known vulnerabilities
   - Review Bandit and CodeQL findings

3. **Manage deployments:**
   - Use manual workflow dispatch for staging deployments
   - Tag releases for production deployments
   - Monitor deployment status

4. **Maintain coverage:**
   - Aim for ≥85% coverage
   - Review coverage reports in PRs
   - Add tests for new features

## Troubleshooting

### CI Tests Failing

1. **Check test logs** in GitHub Actions
2. **Run tests locally** to reproduce:
   ```bash
   pytest tests/ -v
   ```
3. **Check for environment-specific issues** (API keys, network access)

### Coverage Not Uploading

1. **Verify Codecov token** is set (optional, not required)
2. **Check Codecov service status**
3. **Review upload logs** in CI output

### Deployment Failures

1. **Verify secrets** are correctly set
2. **Check deployment platform status**
3. **Review deployment logs** in GitHub Actions
4. **Test deployment manually** before troubleshooting

### Docker Build Failures

1. **Check Dockerfile syntax**
2. **Verify all dependencies** are in requirements.txt
3. **Review build logs** for specific errors
4. **Test build locally:**
   ```bash
   docker build -t shortstory .
   ```

## Future Improvements

Potential enhancements to the CI/CD pipeline:

- [ ] Add performance benchmarking
- [ ] Add load testing with k6 or Locust
- [ ] Add E2E browser testing with Playwright
- [ ] Add automated dependency PR merging (with approval)
- [ ] Add deployment rollback automation
- [ ] Add staging environment for pre-production testing
- [ ] Add automated changelog generation
- [ ] Add semantic versioning automation
- [ ] Add release notes generation

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
