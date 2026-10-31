# doc_parser.py: splits markdown documentation into sections by heading
import re
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
from config import DOC_EXTENSIONS, SKIP_DIRS


class DocSection(BaseModel):
    # A documentation section with heading path, content, and referenced code symbols
    id: str
    file_path: str
    heading_path: str
    content: str
    code_references: List[str]


class DocParser:
    # Parses markdown documentation files into sections keyed by heading path

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def parse_docs(self) -> List[DocSection]:
        # Walk the docs directory and extract all sections from markdown files
        sections: List[DocSection] = []
        for file_path in self._walk_files():
            try:
                file_sections = self.parse_file(file_path)
                sections.extend(file_sections)
            except Exception:
                continue
        return sections

    def _walk_files(self) -> List[Path]:
        # Recursively find all documentation files, skipping ignored directories
        files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for filename in filenames:
                if Path(filename).suffix in DOC_EXTENSIONS:
                    files.append(Path(dirpath) / filename)
        return files

    def parse_file(self, file_path: Path) -> List[DocSection]:
        # Parse a single markdown file into sections by heading
        import os

        relative_path = str(file_path.relative_to(self.root_dir))
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []

        sections: List[DocSection] = []
        # Split by markdown headings (#, ##, ###, etc.)
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(content))

        if not matches:
            # No headings: treat entire file as one section
            code_refs = self._extract_code_references(content)
            sections.append(DocSection(
                id=f"{relative_path}::root",
                file_path=relative_path,
                heading_path="root",
                content=content,
                code_references=code_refs,
            ))
            return sections

        for i, match in enumerate(matches):
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start_pos:end_pos].strip()

            # Build heading path from all headings up to this one
            heading_path = self._build_heading_path(content, match.start(), level, matches[:i + 1])

            code_refs = self._extract_code_references(section_content)
            section_id = f"{relative_path}::{heading_path}"
            sections.append(DocSection(
                id=section_id,
                file_path=relative_path,
                heading_path=heading_path,
                content=section_content,
                code_references=code_refs,
            ))

        return sections

    def _build_heading_path(self, content: str, pos: int, level: int, prior_matches: List) -> str:
        # Construct a dotted heading path like "Configuration > Environment Variables"
        path_parts = []
        for m in prior_matches:
            m_level = len(m.group(1))
            m_text = m.group(2).strip()
            if m_level <= level:
                path_parts.append(m_text)
        if not path_parts:
            path_parts.append("root")
        return " > ".join(path_parts)

    def _extract_code_references(self, content: str) -> List[str]:
        # Extract function names, class names, config keys, and CLI commands mentioned in docs
        references: List[str] = []
        # Inline code references like `function_name`
        inline_refs = re.findall(r"`([^`]+)`", content)
        references.extend(inline_refs)
        # Code block references
        code_blocks = re.findall(r"```\w*\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            refs = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", block)
            references.extend(refs[:20])
        return list(dict.fromkeys(references))
