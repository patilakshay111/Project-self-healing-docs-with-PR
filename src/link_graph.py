# link_graph.py: builds and persists the code-to-docs link graph using embeddings and heuristics
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings
from config import SIMILARITY_THRESHOLD, CHROMA_PERSIST_DIR
from parser import CodeChunk
from doc_parser import DocSection


class Link(BaseModel):
    # A link between a doc section and a code chunk
    doc_section_id: str
    code_chunk_id: str
    link_type: str
    score: float


class LinkGraph:
    # Manages the bipartite graph connecting documentation sections to code chunks

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.doc_collection = self.client.get_or_create_collection(name="doc_sections")
        self.code_collection = self.client.get_or_create_collection(name="code_chunks")
        self.links_file = Path(persist_dir) / "links.json"
        self.links: List[Link] = self._load_links()

    def _load_links(self) -> List[Link]:
        # Load previously saved links from disk
        if self.links_file.exists():
            try:
                with open(self.links_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [Link(**item) for item in data]
            except Exception:
                return []
        return []

    def _save_links(self) -> None:
        # Persist the current links to disk
        with open(self.links_file, "w", encoding="utf-8") as f:
            json.dump([link.dict() for link in self.links], f, indent=2)

    def index_code_chunks(self, chunks: List[CodeChunk]) -> None:
        # Store code chunks in ChromaDB with their embeddings
        if not chunks:
            return
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "file_path": chunk.file_path,
                "element_type": chunk.element_type,
                "name": chunk.name,
                "docstring": chunk.docstring or "",
            }
            for chunk in chunks
        ]
        self.code_collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def index_doc_sections(self, sections: List[DocSection]) -> None:
        # Store doc sections in ChromaDB with their embeddings
        if not sections:
            return
        ids = [section.id for section in sections]
        documents = [section.content for section in sections]
        metadatas = [
            {
                "file_path": section.file_path,
                "heading_path": section.heading_path,
            }
            for section in sections
        ]
        self.doc_collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def build_heuristic_links(self, chunks: List[CodeChunk], sections: List[DocSection]) -> List[Link]:
        # Link doc sections to code chunks using simple name-matching heuristics
        links: List[Link] = []
        chunk_by_name: Dict[str, CodeChunk] = {}
        for chunk in chunks:
            chunk_by_name[chunk.name.lower()] = chunk

        for section in sections:
            for ref in section.code_references:
                ref_lower = ref.lower()
                if ref_lower in chunk_by_name:
                    chunk = chunk_by_name[ref_lower]
                    links.append(Link(
                        doc_section_id=section.id,
                        code_chunk_id=chunk.id,
                        link_type="heuristic",
                        score=1.0,
                    ))
        return links

    def build_embedding_links(self, chunks: List[CodeChunk], sections: List[DocSection]) -> List[Link]:
        # Link doc sections to code chunks using embedding similarity
        links: List[Link] = []
        if not chunks or not sections:
            return links

        chunk_ids = [chunk.id for chunk in chunks]
        section_ids = [section.id for section in sections]

        # Query each doc section against the code chunk collection
        for section in sections:
            results = self.code_collection.query(
                query_texts=[section.content],
                n_results=min(5, len(chunks)),
            )
            if not results["ids"] or not results["ids"][0]:
                continue
            for i, chunk_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if "distances" in results else 0.0
                score = 1.0 - distance
                if score >= SIMILARITY_THRESHOLD:
                    links.append(Link(
                        doc_section_id=section.id,
                        code_chunk_id=chunk_id,
                        link_type="embedding",
                        score=score,
                    ))

        return links

    def build(self, chunks: List[CodeChunk], sections: List[DocSection]) -> List[Link]:
        # Build the complete link graph using both heuristics and embeddings
        self.index_code_chunks(chunks)
        self.index_doc_sections(sections)

        heuristic_links = self.build_heuristic_links(chunks, sections)
        embedding_links = self.build_embedding_links(chunks, sections)

        # Merge links, preferring higher scores
        seen: Dict[Tuple[str, str], Link] = {}
        for link in heuristic_links + embedding_links:
            key = (link.doc_section_id, link.code_chunk_id)
            if key not in seen or link.score > seen[key].score:
                seen[key] = link

        self.links = list(seen.values())
        self._save_links()
        return self.links

    def find_affected_docs(self, code_chunk_ids: List[str]) -> List[str]:
        # Given changed code chunk IDs, return the doc section IDs that might be affected
        affected: set = set()
        for link in self.links:
            if link.code_chunk_id in code_chunk_ids:
                affected.add(link.doc_section_id)
        return list(affected)
