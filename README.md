# Self-Healing Technical Documentation

A GitHub Action that monitors a codebase, detects when code changes make documentation inaccurate, identifies the specific stale sections, and either auto-generates a PR with corrected docs or flags the discrepancies for human review. Installable from GitHub Marketplace.

## What It Does

This project lives inside a CI/CD pipeline. It solves a universal engineering pain point that every team has experienced: documentation goes stale when code changes. The system:

1. **Parses the codebase** into semantic chunks (functions, classes, API endpoints, config schemas, CLI commands)
2. **Parses documentation** into sections by heading
3. **Builds a link graph** connecting doc sections to code chunks using heuristics and embeddings
4. **Detects meaningful changes** from git diffs on every PR
5. **Verifies staleness** with an LLM (old code, new code, doc section)
6. **Generates targeted corrections** preserving original style and structure
7. **Validates corrections** with a second LLM pass before creating a PR
8. **Posts PR comments** summarizing results

## Tech Stack

| Component | Tool / Library | Why This Choice |
|---|---|---|
| Language | Python 3.11+ | Works in GitHub Actions |
| Embeddings | OpenAI text-embedding-3-small | Cheap, fast, high quality |
| Vector Store | ChromaDB (file-based) | No server needed; persists to disk |
| LLM | GPT-4o / GPT-4o-mini | Strong code understanding |
| Git Integration | PyGithub + git diff | PR creation and diff parsing |
| CI/CD | GitHub Actions | Native integration, free tier |
| Containerization | Docker | Reproducible runs |

## Project Structure

```
self_healing_docs_project/
├── .env.example              # Template for API keys
├── .gitignore                # Ignore .env, __pycache__, .chroma/
├── requirements.txt          # pip dependencies
├── config.py                 # Business/config settings
├── main.py                   # Core pipeline orchestration
├── streamlit_app.py          # Streamlit UI for local demo
├── Dockerfile                # Container for GitHub Action
├── action.yml                # GitHub Action definition
├── README.md                 # This file
├── docs/                     # Sample documentation
│   └── api.md
├── src/
│   ├── parser.py             # Codebase parser (semantic chunks)
│   ├── doc_parser.py         # Documentation parser (sections by heading)
│   ├── link_graph.py         # Code-to-docs link graph (ChromaDB)
│   ├── change_detector.py    # Git diff parsing and change detection
│   └── repair_engine.py      # LLM-based staleness check and correction
└── .github/workflows/
    └── doc-healer.yml        # GitHub Actions workflow
```

## Setup

### 1. Clone and install

```bash
git init
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-your-key-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
GITHUB_TOKEN=ghp_your-token-here
CONFIDENCE_THRESHOLD=0.75
AUTO_MERGE_HIGH_CONFIDENCE=false
```

### 3. Run locally

```bash
python main.py
```

Or run the Streamlit UI:

```bash
streamlit run streamlit_app.py
```

### 4. Use as a GitHub Action (Install from Marketplace)

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
        uses: YOUR_USERNAME/self-healing-docs@v0.1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          slack_webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
          confidence_threshold: '0.75'
          auto_merge_high_confidence: 'false'
```

Replace `YOUR_USERNAME` with your GitHub username.

#### Required Secrets

Add these in your repository **Settings → Secrets and variables → Actions**:

| Secret | Required | Description |
|--------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `SLACK_WEBHOOK_URL` | No | Slack webhook URL for alerts |
| `GITHUB_TOKEN` | No | Auto-provided by GitHub (`${{ secrets.GITHUB_TOKEN }}`) |

#### How to Publish to the GitHub Actions Marketplace

1. Make this repository **public** (Settings → General → Danger Zone → Change repository visibility)
2. Push a release tag (see below)
3. GitHub automatically indexes public repos with a valid `action.yml` — your action will appear on [GitHub Marketplace](https://github.com/marketplace)

#### Create and Push the v0.1 Tag

```bash
git tag -a v0.1 -m "Release v0.1: initial public version"
git push origin v0.1
```

Users can now install your action with:

```yaml
- uses: YOUR_USERNAME/self-healing-docs@v0.1
```

## Sample Documentation

The `docs/` folder contains sample API documentation. When you change code that affects documented endpoints, the system will detect the staleness and propose corrections.

## How It Works (Interview Talking Points)

- **Code-to-docs mapping**: Parses code into semantic chunks and docs into sections, then links them via heuristics and embeddings (ChromaDB)
- **Change detection**: Parses git diffs, filters for meaningful changes (API signatures, config, new/removed features), maps to affected doc sections
- **Staleness verification**: LLM compares old code, new code, and doc content to determine if docs are still accurate
- **Targeted correction**: LLM rewrites only stale parts, preserving style and structure; a second LLM validates before PR creation
- **Confidence-based routing**: High confidence → auto-fix PR; low confidence → flag for human review with PR comment
- **ChromaDB**: Local vector store for embedding-based linking, no database server needed
- **GitHub Actions**: Runs on every PR, posts summary comments, creates fix PRs

## What to Avoid

- No hardcoded API keys (use `.env` and secrets)
- No separator lines in code (use blank lines and `#` comments)
- No overly complex logic in single functions (keep nodes small and focused)
- No external databases for the demo (ChromaDB is file-based)

## Author

Akshay Patil

## License

MIT
