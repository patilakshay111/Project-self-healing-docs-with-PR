# main.py: core orchestration for the self-healing docs pipeline
import os
import sys
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import OPENAI_API_KEY, GITHUB_TOKEN, AUTO_MERGE_HIGH_CONFIDENCE
from parser import CodeParser, CodeChunk
from doc_parser import DocParser, DocSection
from link_graph import LinkGraph
from change_detector import ChangeDetector, CodeChange
from repair_engine import RepairEngine, Correction


def run_pipeline(repo_path: str = ".", docs_path: str = "docs") -> Dict:
    # Run the full self-healing docs pipeline: parse, link, detect, repair
    print("[1/5] Parsing codebase into semantic chunks...")
    code_parser = CodeParser(repo_path)
    chunks = code_parser.parse_codebase()
    print(f"    Found {len(chunks)} code chunks")

    print("[2/5] Parsing documentation into sections...")
    doc_parser = DocParser(docs_path)
    sections = doc_parser.parse_docs()
    print(f"    Found {len(sections)} doc sections")

    print("[3/5] Building code-to-docs link graph...")
    link_graph = LinkGraph()
    links = link_graph.build(chunks, sections)
    print(f"    Created {len(links)} links")

    print("[4/5] Detecting code changes from git diff...")
    detector = ChangeDetector(repo_path)
    changes = detector.detect_changes()
    print(f"    Found {len(changes)} meaningful changes")

    print("[5/5] Checking staleness and generating corrections...")
    repair_engine = RepairEngine()
    all_corrections: List[Correction] = []

    for change in changes:
        affected_doc_ids = link_graph.find_affected_docs([change.file_path])
        suspects = [s for s in sections if s.id in affected_doc_ids]
        if not suspects:
            continue
        corrections = repair_engine.process_suspects(
            suspects,
            change.old_code or "",
            change.new_code or "",
        )
        all_corrections.extend(corrections)

    return {
        "chunks": chunks,
        "sections": sections,
        "links": links,
        "changes": changes,
        "corrections": all_corrections,
    }


def print_results(results: Dict) -> None:
    # Print a summary of the pipeline results
    print("\n=== Self-Healing Docs Results ===")
    print(f"Code chunks: {len(results['chunks'])}")
    print(f"Doc sections: {len(results['sections'])}")
    print(f"Links: {len(results['links'])}")
    print(f"Changes: {len(results['changes'])}")
    print(f"Corrections: {len(results['corrections'])}")

    for correction in results["corrections"]:
        print(f"\n  Correction: {correction.doc_section_id}")
        print(f"    Mode: {correction.correction_mode}")
        print(f"    Confidence: {correction.confidence:.2f}")


if __name__ == "__main__":
    load_dotenv()
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set. Copy .env.example to .env and fill in your key.")
        sys.exit(1)

    results = run_pipeline()
    print_results(results)
