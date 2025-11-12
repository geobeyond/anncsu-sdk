# GitHub Actions Workflows

## Publish to PyPI

**File**: `publish.yml`

### Overview

This workflow automatically publishes the ANNCSU SDK to PyPI when code is pushed to the `main` branch.

### Triggers

The workflow runs on:
- ✅ Push to `main` branch
- ❌ Ignores changes to:
  - Markdown files (`**.md`)
  - Documentation (`docs/**`)
  - GitHub workflows (except `publish.yml` itself)

### Prerequisites

Before this workflow can run successfully, you need to:

#### 1. Generate a PyPI Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Set token name: `anncsu-sdk-github-actions`
4. For first publish: Select "Entire account"
5. After first publish: Create a new token scoped to "Project: anncsu-sdk"
6. Copy the token (shown only once!)

#### 2. Add Token to GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `PYPI_TOKEN`
5. Value: Paste your PyPI token (starts with `pypi-`)
6. Click **"Add secret"**

### Workflow Steps

1. **Checkout code**: Fetches the repository with full history for versioning
2. **Set up Python**: Installs Python 3.12
3. **Install uv**: Installs the uv package manager
4. **Install dependencies**: Syncs all dependencies including dev packages
5. **Run tests**: Executes all 329 tests
6. **Run ruff checks**: Validates code quality and style
7. **Build package**: Creates distribution packages (wheel and sdist)
8. **Publish to PyPI**: Uploads the package to PyPI
9. **Create GitHub Release**: Creates a release if a tag is pushed (optional)

### Version Management

The SDK uses `uv-dynamic-versioning` which automatically determines the version from git:

- **Commits on main**: `0.0.X.devN+<commit-hash>`
- **Tagged commits**: Uses the tag version (e.g., `v1.0.0` → `1.0.0`)

### How to Publish

#### Automatic (Recommended)

Simply merge or push to the `main` branch:

```bash
# Merge your feature branch to main
git checkout main
git merge feature/my-feature
git push origin main

# The workflow will automatically:
# 1. Run tests
# 2. Build the package
# 3. Publish to PyPI
```

#### Manual Release with Tags

For versioned releases:

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# This will:
# 1. Publish version 1.0.0 to PyPI
# 2. Create a GitHub Release
```

### Monitoring

To view workflow runs:

1. Go to your repository on GitHub
2. Click the **"Actions"** tab
3. Select **"Publish to PyPI"** workflow
4. View the latest runs and their status

### Troubleshooting

#### ❌ "PYPI_TOKEN secret not found"

**Solution**: Add the `PYPI_TOKEN` secret to your repository (see Prerequisites above)

#### ❌ "Package already exists on PyPI"

**Cause**: The version already exists on PyPI

**Solutions**:
- Commit more changes to increment the dev version
- Create a new tag for a release version
- Check your versioning strategy

#### ❌ "Tests failed"

**Cause**: One or more tests are failing

**Solution**: Fix the failing tests before merging to main

#### ❌ "Ruff checks failed"

**Cause**: Code quality/style issues detected

**Solution**: Run `uv run ruff check . --fix` locally and commit the fixes

### Security Best Practices

✅ **Do:**
- Use project-scoped tokens (after first upload)
- Rotate tokens periodically
- Only give the workflow `contents: read` permission
- Review all PRs before merging to main

❌ **Don't:**
- Commit the PyPI token to the repository
- Share the token publicly
- Use account-wide tokens in production

### Optional: Trusted Publishing (More Secure)

PyPI supports "Trusted Publishing" which eliminates the need for tokens:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new "pending publisher"
3. Fill in:
   - **PyPI Project Name**: `anncsu-sdk`
   - **Owner**: Your GitHub username or org
   - **Repository name**: `anncsu-sdk`
   - **Workflow name**: `publish.yml`
   - **Environment name**: (leave blank)

4. Update the workflow to use OIDC:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    packages-dir: dist/
```

This way you don't need to manage tokens at all!

### Local Publishing

To publish manually without GitHub Actions:

```bash
# Set your PyPI token
export PYPI_TOKEN="pypi-AgEIcHlwaS5vcmc..."

# Run the publish script
./scripts/publish.sh
```

### References

- [PyPI Help - API Tokens](https://pypi.org/help/#apitoken)
- [GitHub Actions - Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
