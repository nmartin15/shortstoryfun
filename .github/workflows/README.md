# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD automation.

## Quick Start

1. **Push to GitHub**: The workflows will automatically run on push/PR
2. **Set up secrets** (optional, for deployment):
   - Go to Settings → Secrets and variables → Actions
   - Add required secrets (see CI_CD.md for details)
3. **Enable Codecov** (optional, for coverage):
   - Sign up at codecov.io
   - Add your repository

## Workflows

- **ci.yml**: Main CI pipeline (testing, coverage, quality checks)
- **deploy.yml**: Deployment automation (Heroku, Railway, Render, Docker)
- **security.yml**: Security scanning (dependencies, code analysis)
- **codeql.yml**: GitHub CodeQL security analysis

## Workflow Status

View workflow runs at: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

## Documentation

See [CI_CD.md](../../CI_CD.md) for detailed documentation.
