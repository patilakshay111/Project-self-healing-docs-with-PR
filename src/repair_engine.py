# repair_engine.py: uses LLMs to verify doc staleness and generate targeted corrections
import os
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from openai import OpenAI
from config import OPENAI_API_KEY, CONFIDENCE_THRESHOLD, AUTO_MERGE_HIGH_CONFIDENCE
from parser import CodeChunk
from doc_parser import DocSection
from link_graph import Link


class StalenessCheck(BaseModel):
    # Result of checking whether a doc section is still accurate given code changes
    is_stale: bool
    confidence: float
    explanation: str
    specific_issues: List[str]


class Correction(BaseModel):
    # A proposed correction for a stale doc section
    doc_section_id: str
    original_content: str
    corrected_content: str
    confidence: float
    correction_mode: str


class RepairEngine:
    # Verifies staleness with an LLM and generates targeted corrections for doc sections

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def check_staleness(self, old_code: str, new_code: str, doc_section: DocSection) -> StalenessCheck:
        # Ask the LLM whether the doc section is still accurate given the code change
        prompt = f"""
You are a documentation accuracy checker. Given the old code, new code, and a documentation section, determine if the documentation is still accurate.

OLD CODE:
{old_code}

NEW CODE:
{new_code}

DOCUMENTATION SECTION ({doc_section.heading_path}):
{doc_section.content}

CODE REFERENCES IN DOC: {', '.join(doc_section.code_references)}

Respond with JSON:
{{
  "is_stale": true/false,
  "confidence": 0.0 to 1.0,
  "explanation": "brief explanation",
  "specific_issues": ["issue1", "issue2"]
}}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        import json
        try:
            data = json.loads(content)
        except Exception:
            data = {"is_stale": False, "confidence": 0.0, "explanation": "parse error", "specific_issues": []}

        return StalenessCheck(
            is_stale=data.get("is_stale", False),
            confidence=float(data.get("confidence", 0.0)),
            explanation=data.get("explanation", ""),
            specific_issues=data.get("specific_issues", []),
        )

    def generate_correction(self, doc_section: DocSection, new_code: str, staleness: StalenessCheck) -> Correction:
        # Rewrite only the stale parts of a doc section, preserving style and structure
        prompt = f"""
You are a documentation repair assistant. Rewrite only the stale parts of this documentation section based on the new code.

CURRENT DOC SECTION ({doc_section.heading_path}):
{doc_section.content}

NEW CODE:
{new_code}

STALENESS DIAGNOSIS:
{staleness.explanation}
Specific issues: {', '.join(staleness.specific_issues)}

Instructions:
- Preserve the original style, tone, and structure
- Only rewrite parts that are now inaccurate
- Do NOT rewrite parts that are still accurate
- Output only the corrected documentation section

Return the corrected content as plain text.
"""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        corrected_content = response.choices[0].message.content or doc_section.content

        # Determine correction mode based on confidence
        if staleness.confidence >= 0.85:
            correction_mode = "auto_fix"
        elif staleness.confidence >= CONFIDENCE_THRESHOLD:
            correction_mode = "auto_fix"
        else:
            correction_mode = "human_review"

        return Correction(
            doc_section_id=doc_section.id,
            original_content=doc_section.content,
            corrected_content=corrected_content,
            confidence=staleness.confidence,
            correction_mode=correction_mode,
        )

    def validate_correction(self, doc_section: DocSection, correction: Correction, new_code: str) -> bool:
        # Second LLM pass to verify the correction is accurate and preserves correct parts
        prompt = f"""
You are a documentation quality gate. Check if the corrected documentation accurately describes the new code and preserves parts that were already correct.

ORIGINAL DOC:
{doc_section.content}

CORRECTED DOC:
{correction.corrected_content}

NEW CODE:
{new_code}

Respond with JSON:
{{
  "accurate": true/false,
  "preserved_correct_parts": true/false,
  "style_consistent": true/false,
  "passes_quality_gate": true/false
}}
"""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        import json
        try:
            data = json.loads(content)
        except Exception:
            return False

        return data.get("passes_quality_gate", False)

    def process_suspects(self, suspects: List[DocSection], old_code: str, new_code: str) -> List[Correction]:
        # For each suspect doc section, check staleness and generate corrections if needed
        corrections: List[Correction] = []
        for section in suspects:
            staleness = self.check_staleness(old_code, new_code, section)
            if staleness.is_stale and staleness.confidence >= CONFIDENCE_THRESHOLD:
                correction = self.generate_correction(section, new_code, staleness)
                if self.validate_correction(section, correction, new_code):
                    corrections.append(correction)
        return corrections
