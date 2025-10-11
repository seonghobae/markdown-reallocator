# CI/CD Setup Guide

This document explains how to set up and configure CI/CD for the Markdown Reallocator project.

## Overview

The project uses GitHub Actions for continuous integration and deployment:

- **CI Workflow** (`ci.yml`): Runs on every push/PR
- **Release Workflow** (`release.yml`): Publishes to PyPI on version tags
- **Docs Workflow** (`docs.yml`): Deploys documentation to GitHub Pages

## Initial Setup

### 1. Enable GitHub Actions

GitHub Actions is enabled by default for public repositories. For private repositories:

1. Go to repository Settings → Actions → General
2. Select "Allow all actions and reusable workflows"
3. Click "Save"

### 2. Configure Branch Protection

Protect the `main` branch to require CI checks:

1. Go to Settings → Branches → Add branch protection rule
2. Branch name pattern: `main`
3. Check "Require status checks to pass before merging"
4. Select required checks:
   - `Lint`
   - `Test - Python 3.10`
   - `Test - Python 3.11`
   - `Test - Python 3.12`
   - `Performance Benchmarks`
5. Check "Require branches to be up to date before merging"
6. Check "Require conversation resolution before merging"
7. Click "Create"

### 3. Setup Codecov (Optional but Recommended)

For coverage reporting:

1. Go to https://codecov.io
2. Sign in with GitHub
3. Enable your repository
4. Copy the upload token
5. Add to repository secrets:
   - Settings → Secrets and variables → Actions → New repository secret
   - Name: `CODECOV_TOKEN`
   - Value: [your token]

### 4. Setup PyPI Publishing

For automated releases to PyPI:

1. Create a PyPI account at https://pypi.org
2. Generate an API token:
   - Account settings → API tokens → Add API token
   - Token name: `github-actions-markdown-reallocator`
   - Scope: "Entire account" or "Project: markdown-reallocator"
3. Add to repository secrets:
   - Settings → Secrets and variables → Actions → New repository secret
   - Name: `PYPI_API_TOKEN`
   - Value: `pypi-[your-token]`

### 5. Enable GitHub Pages

For documentation deployment:

1. Go to Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `gh-pages` / `/ (root)`
4. Click "Save"

The documentation will be available at: `https://yourusername.github.io/markdown-reallocator/`

### 6. Install Pre-commit Hooks (Local Development)

For local development, install pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files (optional)
pre-commit run --all-files
```

## Workflows

### CI Workflow

**Triggers**: Push to main/develop, Pull requests

**Jobs**:
1. **Lint**: Runs ruff and mypy
2. **Test**: Runs tests on Python 3.10, 3.11, 3.12
3. **Benchmark**: Runs performance benchmarks

**Configuration**: `.github/workflows/ci.yml`

### Release Workflow

**Triggers**: Push tags matching `v*` (e.g., `v0.1.0`)

**Jobs**:
1. **Test**: Full test suite
2. **Build**: Build distributions (wheel + sdist)
3. **Publish**: Upload to PyPI
4. **Create Release**: GitHub release with changelog

**Configuration**: `.github/workflows/release.yml`

**Usage**:
```bash
# Create and push a version tag
git tag v0.1.0
git push origin v0.1.0
```

### Docs Workflow

**Triggers**: Push to main branch (documentation changes)

**Jobs**:
1. **Deploy**: Build and deploy to GitHub Pages

**Configuration**: `.github/workflows/docs.yml`

## Dependabot

Dependabot automatically creates PRs for dependency updates.

**Configuration**: `.github/dependabot.yml`

**Features**:
- Weekly updates for Python dependencies
- Weekly updates for GitHub Actions
- Grouped updates for dev/production dependencies
- Auto-labeling and reviewers

## Status Badges

Status badges in README.md:

```markdown
[![CI](https://github.com/yourusername/markdown-reallocator/workflows/CI/badge.svg)](...)
[![codecov](https://codecov.io/gh/yourusername/markdown-reallocator/branch/main/graph/badge.svg)](...)
[![PyPI version](https://badge.fury.io/py/markdown-reallocator.svg)](...)
```

Replace `yourusername` with your actual GitHub username.

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

**Hooks**:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Ruff linting and formatting
- MyPy type checking
- Import sorting (isort)

**Configuration**: `.pre-commit-config.yaml`

**Skip hooks** (when needed):
```bash
git commit --no-verify
```

## Troubleshooting

### CI Fails on Import Errors

If CI fails due to missing dependencies:
1. Update `pyproject.toml` dependencies
2. Ensure all imports have corresponding packages

### Coverage Too Low

If coverage check fails:
1. Write more tests
2. Or temporarily lower threshold in `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   addopts = ["--cov-fail-under=80"]  # Adjust threshold
   ```

### Release Fails

If PyPI publish fails:
1. Check `PYPI_API_TOKEN` secret is set correctly
2. Ensure version in `pyproject.toml` is incremented
3. Check package builds locally: `python -m build`

### Docs Not Deploying

If GitHub Pages deployment fails:
1. Check GitHub Pages is enabled (Settings → Pages)
2. Ensure `gh-pages` branch exists
3. Check workflow permissions (Settings → Actions → General → Workflow permissions → Read and write)

## Best Practices

1. **Always run tests locally before pushing**:
   ```bash
   pytest tests/
   ```

2. **Use pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Test benchmarks locally**:
   ```bash
   pytest benchmarks/ --benchmark-only
   ```

4. **Lint before committing**:
   ```bash
   ruff check .
   mypy markdown_reallocator
   ```

5. **Version tags follow SemVer**:
   - `v0.1.0`: Initial release
   - `v0.1.1`: Bug fixes
   - `v0.2.0`: New features
   - `v1.0.0`: Stable release

## Security

- **Never commit secrets** to the repository
- Use GitHub Secrets for sensitive data
- Dependabot PRs should be reviewed before merging
- Enable "Require approval for all outside collaborators" in Actions settings
