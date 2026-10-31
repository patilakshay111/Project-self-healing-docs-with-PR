# Load configuration from environment variables for the self-healing docs project
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Slack webhook for alerts
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# GitHub token for PR creation and diff parsing
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Confidence threshold for auto-fixing vs human review
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# Whether to auto-merge high-confidence fixes
AUTO_MERGE_HIGH_CONFIDENCE = os.getenv("AUTO_MERGE_HIGH_CONFIDENCE", "false").lower() == "true"

# ChromaDB persistence directory for the code-to-docs link graph
CHROMA_PERSIST_DIR = ".chroma"

# Directories to skip when parsing the codebase
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".chroma"}

# File extensions to parse for code chunks
CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java"}

# Documentation file extensions
DOC_EXTENSIONS = {".md", ".mdx", ".rst"}

# Maximum number of characters per code chunk
MAX_CHUNK_CHARS = 2000

# Similarity threshold for linking doc sections to code chunks via embeddings
SIMILARITY_THRESHOLD = 0.7
