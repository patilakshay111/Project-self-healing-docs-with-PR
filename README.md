# Self-Healing Technical Documentation

A GitHub Action that monitors a codebase, detects when code changes make documentation inaccurate, identifies the specific stale sections, and either auto-generates a PR with corrected docs or flags the discrepancies for human review.

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

### 4. Use as a GitHub Action

1. Copy `.github/workflows/doc-healer.yml` to your repository
2. Add `OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`, and `GITHUB_TOKEN` as repository secrets
3. Push a PR that modifies code files - the Action will run automatically

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

## License

MIT
