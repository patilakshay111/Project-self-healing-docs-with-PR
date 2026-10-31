# change_detector.py: parses git diffs and identifies meaningful code changes that affect docs
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional
from pydantic import BaseModel
from config import CODE_EXTENSIONS
from parser import CodeChunk


class CodeChange(BaseModel):
    # A single meaningful change detected in the codebase
    file_path: str
    change_type: str
    old_code: Optional[str]
    new_code: Optional[str]
    affected_chunks: List[str]


class ChangeDetector:
    # Detects meaningful code changes from git diffs and maps them to code chunks

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def get_changed_files(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> List[str]:
        # Return the list of files changed between two git refs
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base_ref, target_ref],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
            return [f for f in files if Path(f).suffix in CODE_EXTENSIONS]
        except Exception:
            return []

    def get_diff_for_file(self, file_path: str, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> str:
        # Return the unified diff for a specific file between two refs
        try:
            result = subprocess.run(
                ["git", "diff", base_ref, target_ref, "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except Exception:
            return ""

    def is_meaningful_change(self, file_path: str, diff: str) -> bool:
        # Determine if a diff represents a meaningful change that could affect documentation
        if not diff.strip():
            return False

        # Skip comment-only and whitespace-only changes
        diff_lines = diff.split("\n")
        added_lines = [l for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
        removed_lines = [l for l in diff_lines if l.startswith("-") and not l.startswith("---")]

        # Filter out comment-only changes
        meaningful_added = [l for l in added_lines if not self._is_comment_only(l[1:])]
        meaningful_removed = [l for l in removed_lines if not self._is_comment_only(l[1:])]

        if not meaningful_added and not meaningful_removed:
            return False

        # Skip test files
        if "test" in file_path.lower():
            return False

        # Focus on: API signature changes, config changes, new/removed features, behavioral changes
        meaningful_patterns = [
            r"def\s+\w+",
            r"class\s+\w+",
            r"@\w+",
            r"APP\.|app\.|router\.",
            r"CONFIG|config|settings|env",
            r"import\s+|from\s+",
            r"return\s+",
            r"->\s*\w+",
        ]

        all_changes = "\n".join(meaningful_added + meaningful_removed)
        for pattern in meaningful_patterns:
            if re.search(pattern, all_changes):
                return True

        return False

    def _is_comment_only(self, line: str) -> bool:
        # Check if a line is only a comment or whitespace
        stripped = line.strip()
        return stripped == "" or stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*")

    def detect_changes(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> List[CodeChange]:
        # Detect all meaningful code changes and map them to affected code chunks
        changed_files = self.get_changed_files(base_ref, target_ref)
        changes: List[CodeChange] = []

        for file_path in changed_files:
            diff = self.get_diff_for_file(file_path, base_ref, target_ref)
            if not self.is_meaningful_change(file_path, diff):
                continue

            added_lines = [l[1:] for l in diff.split("\n") if l.startswith("+") and not l.startswith("+++")]
            removed_lines = [l[1:] for l in diff.split("\n") if l.startswith("-") and not l.startswith("---")]

            changes.append(CodeChange(
                file_path=file_path,
                change_type="modified",
                old_code="\n".join(removed_lines) if removed_lines else None,
                new_code="\n".join(added_lines) if added_lines else None,
                affected_chunks=[],
            ))

        return changes
