# Quarto Build Action

A composite GitHub Action for building Quarto projects with Python, Node.js, Julia, and PDF generation support.

## Features

- **Multi-language support**: Python (uv), Julia within Quarto
- **Smart caching**: Jupyter cache, Julia cache, and PDF cache with branch isolation
- **PDF generation**: Optional slide PDF generation using Decktape
- **Artifact management**: Automatic upload of rendered site and notebooks
- **Flexible configuration**: Customizable via inputs with sensible defaults

## Usage

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - uses: HighDimensionalEconLab/actions/quarto-build@v1
        with:
          apt-packages: 'ffmpeg graphviz'
          quarto-profile: 'lectures'
          build-slide-pdfs: 'true'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `apt-packages` | Space-separated list of apt packages to install | No | `ffmpeg graphviz` |
| `pdf-cache-dir` | Directory for PDF cache | No | `.pdf_cache` |
| `quarto-args` | Additional arguments to pass to quarto render | No | `''` |
| `quarto-profile` | Quarto profile(s) to use (comma-separated) | No | `lectures` |
| `output-dir` | Output directory for rendered Quarto project | No | `.lectures_output` |
| `artifact-name` | Name for the notebooks artifact | No | `notebooks` |
| `notebooks-source-dir` | Directory with additional notebook files to copy | No | `notebooks_repo` |
| `upload-notebooks` | Whether to upload the notebooks artifact | No | `true` |
| `node-version` | Node.js version for PDF generation | No | `20` |
| `build-slide-pdfs` | Whether to build slide PDFs using decktape | No | `true` |

## Requirements

Your repository should include:

- **`.quarto-version`**: Quarto version (empty string or omit for latest)
- **`.julia-version`**: Julia version (optional, only if using Julia)
- **`pyproject.toml`**: Python dependencies for uv
- **Environment variables**: Any secrets like `OPENAI_API_KEY` should be set in the calling workflow

## Outputs

The action generates and uploads:

1. **Pages artifact**: Rendered Quarto site (always uploaded)
2. **Notebooks artifact**: Extracted notebooks with dependencies (optional)

## Example Workflow

```yaml
name: Build and Deploy Quarto Project

on:
  push:
    branches: [main]

env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Build Quarto Project
        uses: HighDimensionalEconLab/actions/quarto-build@v1
        with:
          apt-packages: 'ffmpeg graphviz'
          quarto-profile: 'lectures'
          output-dir: '.lectures_output'
          build-slide-pdfs: 'true'

  deploy:
    needs: build
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## Caching

The action implements intelligent caching:

- **Jupyter cache** (`**/.jupyter_cache/**`): Python notebook execution results
- **Julia cache** (`**/.cache/**`): Julia notebook execution results
- **PDF cache**: Generated slide PDFs (only regenerates when source changes)

All caches use branch-isolated keys with SHA-based versioning for incremental updates.

## License

MIT
