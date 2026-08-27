"""Validation layer: every escalation / red-flag instruction in the source protocol must survive
into the structured output. An LLM silently dropping an escalation criterion is a safety issue for
a healthcare-adjacent tool, not just a formatting bug -- this check exists to catch that case.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Set

from .schema import ProtocolOutput

ESCALATION_TRIGGER_PATTERNS = [
    r"escalat\w*",
    r"notify\w*",
    r"refer\w*\s+to\s+(the\s+)?(physician|doctor|cardiolog\w*)",
    r"call\w*\s+(the\s+)?(physician|doctor|cardiolog\w*)",
    r"seek\s+(immediate|emergency)",
    r"stop\s+(exercise|the\s+session)",
    r"do\s+not\s+exercise",
    r"skip\s+exercise",
]
_TRIGGER_RE = re.compile("|".join(ESCALATION_TRIGGER_PATTERNS), re.IGNORECASE)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "if", "at", "that",
    "this", "should", "be", "with", "per", "day", "any", "same", "it", "its", "as", "each",
}


@dataclass
class ValidationIssue:
    escalation_sentence: str
    matched_keywords: Set[str] = field(default_factory=set)
    missing_keywords: Set[str] = field(default_factory=set)

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return (
            f"Escalation criterion may be missing from output: \"{self.escalation_sentence}\" "
            f"(no monitoring entry covers: {', '.join(sorted(self.missing_keywords)) or 'n/a'})"
        )


def _split_sentences(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]


def _keywords(text: str) -> Set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def find_escalation_sentences(protocol_text: str) -> List[str]:
    """Keyword-match sentences in the source protocol that describe an escalation / red-flag rule."""
    return [s for s in _split_sentences(protocol_text) if _TRIGGER_RE.search(s)]


def _monitoring_text(output: ProtocolOutput) -> str:
    parts: List[str] = []
    for item in output.session_plan.monitoring:
        parts.extend(v for v in (item.metric, item.threshold, item.action, item.action_if_present) if v)
    return " ".join(parts)


def validate_escalation_coverage(
    protocol_text: str, output: ProtocolOutput, min_overlap: float = 0.3
) -> List[ValidationIssue]:
    """Check that every escalation sentence detected in the source text is reflected in
    session_plan.monitoring. Returns one ValidationIssue per escalation sentence whose keyword
    overlap with the structured monitoring section falls below `min_overlap` -- i.e. a likely
    dropped red-flag / escalation criterion. An empty list means every detected escalation
    sentence has a matching monitoring entry.
    """
    monitoring_keywords = _keywords(_monitoring_text(output))

    issues: List[ValidationIssue] = []
    for sentence in find_escalation_sentences(protocol_text):
        sentence_keywords = _keywords(sentence)
        if not sentence_keywords:
            continue
        matched = sentence_keywords & monitoring_keywords
        if len(matched) / len(sentence_keywords) < min_overlap:
            issues.append(
                ValidationIssue(
                    escalation_sentence=sentence,
                    matched_keywords=matched,
                    missing_keywords=sentence_keywords - matched,
                )
            )
    return issues
