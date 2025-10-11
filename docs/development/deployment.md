# Documentation Deployment

This project uses GitHub Pages to automatically deploy documentation from the main branch.

## Automatic Deployment

The documentation is automatically built and deployed on every push to the main branch via GitHub Actions.

### Workflow Configuration

The deployment workflow is defined in `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main
  workflow_dispatch:
```

### Steps

1. **Checkout**: Fetches the repository code
2. **Setup Python**: Installs Python 3.10
3. **Install Dependencies**: Installs MkDocs and plugins via `pip install -e ".[docs]"`
4. **Build**: Runs `mkdocs build --strict` to generate static site
5. **Deploy**: Pushes the `site/` directory to the `gh-pages` branch

## GitHub Pages Configuration

To enable GitHub Pages for this repository:

1. Go to repository Settings → Pages
2. Under "Source", select "Deploy from a branch"
3. Select the `gh-pages` branch and `/ (root)` folder
4. Click Save

The documentation will be available at: `https://<username>.github.io/<repository>/`

## Local Preview

To preview the documentation locally:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Serve with live reload
mkdocs serve

# Build static site
mkdocs build
```

The development server runs at `http://127.0.0.1:8000/`

## Manual Deployment

To manually deploy documentation:

```bash
# Build and deploy to gh-pages branch
mkdocs gh-deploy

# Or trigger the GitHub Actions workflow
# Go to Actions tab → Deploy Documentation → Run workflow
```

## Troubleshooting

### Build Fails in CI

If the workflow fails:

1. Check the Actions tab for detailed error logs
2. Verify all documentation files exist and are valid markdown
3. Ensure `mkdocs.yml` navigation matches actual file structure
4. Test locally with `mkdocs build --strict`

### 404 on GitHub Pages

If the site shows a 404 error:

1. Verify GitHub Pages is enabled in repository settings
2. Check that the `gh-pages` branch exists and contains the site files
3. Wait a few minutes for GitHub's CDN to update
4. Check the repository visibility (public repos work best)

### Missing Styles or Assets

If the site loads but looks broken:

1. Check the `site_url` in `mkdocs.yml` matches your GitHub Pages URL
2. Verify the `use_directory_urls` setting is appropriate
3. Clear browser cache and reload
