# Release v0.1 — Self-Healing Technical Documentation

## What's New

First public release of the Self-Healing Technical Documentation GitHub Action.

## What This Action Does

Monitors a codebase, detects when code changes make documentation inaccurate, identifies the specific stale sections, and either auto-generates a PR with corrected docs or flags the discrepancies for human review.

## How to Install

Add this to your repository's `.github/workflows/doc-healer.yml`:

```yaml
name: Doc Healer
on:
  pull_request:
    paths:
      - '**.py'
      - '**.ts'
      - '**.tsx'
      - '**.js'
      - '**.jsx'
      - '**.md'

jobs:
  heal-docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Self-Healing Docs
        uses: patilakshay111/Project-self-healing-docs-with-PR@v0.1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          slack_webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
          confidence_threshold: '0.75'
          auto_merge_high_confidence: 'false'
```

## Required Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `SLACK_WEBHOOK_URL` | No | Slack webhook URL for alerts |

## Tech Stack

- Python 3.11+
- OpenAI GPT-4o-mini / GPT-4o
- ChromaDB (file-based vector store)
- Docker container
- GitHub Actions

## Links

- Repository: https://github.com/patilakshay111/Project-self-healing-docs-with-PR
- Documentation: README.md in this repo

---
