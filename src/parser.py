# parser.py: walks the codebase and extracts semantic chunks with stable identifiers
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
from config import SKIP_DIRS, CODE_EXTENSIONS, MAX_CHUNK_CHARS


class CodeChunk(BaseModel):
    # A single semantic unit of code extracted from the codebase
    id: str
    file_path: str
    element_type: str
    name: str
    content: str
    docstring: Optional[str] = None
    line_start: int
    line_end: int


class CodeParser:
    # Parses source files into semantic chunks: functions, classes, endpoints, configs, CLI commands

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def parse_codebase(self) -> List[CodeChunk]:
        # Walk the codebase directory and extract all code chunks from supported files
        chunks: List[CodeChunk] = []
        for file_path in self._walk_files():
            try:
                file_chunks = self.parse_file(file_path)
                chunks.extend(file_chunks)
            except Exception:
                continue
        return chunks

    def _walk_files(self) -> List[Path]:
        # Recursively find all code files, skipping ignored directories
        files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for filename in filenames:
                if Path(filename).suffix in CODE_EXTENSIONS:
                    files.append(Path(dirpath) / filename)
        return files

    def parse_file(self, file_path: Path) -> List[CodeChunk]:
        # Parse a single source file into semantic code chunks
        relative_path = str(file_path.relative_to(self.root_dir))
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception:
            return []

        extension = file_path.suffix
        if extension == ".py":
            return self._parse_python(source, relative_path)
        if extension in {".ts", ".tsx", ".js", ".jsx"}:
            return self._parse_typescript(source, relative_path)
        return []

    def _parse_python(self, source: str, file_path: str) -> List[CodeChunk]:
        # Extract functions, classes, and module-level docstrings from Python source
        chunks: List[CodeChunk] = []
        lines = source.split("\n")

        # Match function definitions
        for match in re.finditer(r"^def\s+(\w+)\s*\([^)]*\):", source, re.MULTILINE):
            name = match.group(1)
            start_line = source[:match.start()].count("\n") + 1
            end_line = self._find_block_end(lines, start_line - 1)
            content = "\n".join(lines[start_line - 1:end_line])
            docstring = self._extract_docstring(content)
            chunk_id = f"{file_path}::{name}"
            chunks.append(CodeChunk(
                id=chunk_id,
                file_path=file_path,
                element_type="function",
                name=name,
                content=content,
                docstring=docstring,
                line_start=start_line,
                line_end=end_line,
            ))

        # Match class definitions
        for match in re.finditer(r"^class\s+(\w+)", source, re.MULTILINE):
            name = match.group(1)
            start_line = source[:match.start()].count("\n") + 1
            end_line = self._find_block_end(lines, start_line - 1)
            content = "\n".join(lines[start_line - 1:end_line])
            docstring = self._extract_docstring(content)
            chunk_id = f"{file_path}::{name}"
            chunks.append(CodeChunk(
                id=chunk_id,
                file_path=file_path,
                element_type="class",
                name=name,
                content=content,
                docstring=docstring,
                line_start=start_line,
                line_end=end_line,
            ))

        return chunks

    def _parse_typescript(self, source: str, file_path: str) -> List[CodeChunk]:
        # Extract functions, classes, and interfaces from TypeScript/JavaScript source
        chunks: List[CodeChunk] = []
        lines = source.split("\n")

        for match in re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", source, re.MULTILINE):
            name = match.group(1)
            start_line = source[:match.start()].count("\n") + 1
            end_line = self._find_block_end(lines, start_line - 1)
            content = "\n".join(lines[start_line - 1:end_line])
            chunk_id = f"{file_path}::{name}"
            chunks.append(CodeChunk(
                id=chunk_id,
                file_path=file_path,
                element_type="function",
                name=name,
                content=content,
                line_start=start_line,
                line_end=end_line,
            ))

        for match in re.finditer(r"(?:export\s+)?class\s+(\w+)", source, re.MULTILINE):
            name = match.group(1)
            start_line = source[:match.start()].count("\n") + 1
            end_line = self._find_block_end(lines, start_line - 1)
            content = "\n".join(lines[start_line - 1:end_line])
            chunk_id = f"{file_path}::{name}"
            chunks.append(CodeChunk(
                id=chunk_id,
                file_path=file_path,
                element_type="class",
                name=name,
                content=content,
                line_start=start_line,
                line_end=end_line,
            ))

        return chunks

    def _find_block_end(self, lines: List[str], start_index: int) -> int:
        # Find the line index where a code block ends based on indentation
        if start_index >= len(lines):
            return start_index + 1
        base_indent = len(lines[start_index]) - len(lines[start_index].lstrip())
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip() == "":
                continue
            indent = len(lines[i]) - len(lines[i].lstrip())
            if indent <= base_indent:
                return i
        return len(lines)

    def _extract_docstring(self, content: str) -> Optional[str]:
        # Extract the first docstring from a code block
        match = re.search(r'"""([^"]+)"""', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"'''([^']+)'''", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
