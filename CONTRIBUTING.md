# Contributing to Self-Healing Technical Documentation

Thank you for considering a contribution! This project is an installable GitHub Action that detects stale documentation and auto-generates fix PRs.

## How to Contribute

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** and test locally
4. **Commit** with a clear message: `git commit -m "Add: describe your change"`
5. **Push** to your fork: `git push origin feature/your-feature-name`
6. **Open a Pull Request** against the `main` branch

## Areas We Welcome Help With

- New language parsers (Java, Go, Rust, etc.)
- Additional LLM providers (Cohere, Mistral, etc.)
- Improved chunking strategies for docs
- More validation rules for business domains
- UI improvements to the Streamlit dashboard
- Documentation and examples

## Code Style

- Every `.py` file starts with a one-line purpose comment
- Every class, function, and major block gets a single-line `#` comment
- Use `pydantic.BaseModel` for data models
- No hardcoded API keys — use `.env` and repository secrets
- No `----` separator lines in code

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
