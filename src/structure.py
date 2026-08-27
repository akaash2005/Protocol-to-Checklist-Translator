"""Protocol text -> structured session plan + QA rubric, via a schema-constrained Claude call."""

from __future__ import annotations

import os

import anthropic

from .schema import ProtocolOutput

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """You are a clinical protocol structuring assistant for Praan Health, a physician-led \
chronic care company. Coaches in different cities must execute a doctor's protocol identically, without \
the doctor in the room, so precision matters more than style.

Given an unstructured clinical protocol written by a doctor, nutritionist, or strength coach, convert it \
into a structured session plan and a QA rubric.

Rules:
- Preserve every clinically meaningful instruction from the source text. Do not invent constraints, \
thresholds, or activities that are not stated or clearly implied by the text.
- Every escalation / red-flag instruction in the source text (for example "escalate to physician if X", \
"stop if Y", "notify care coordinator if Z") MUST appear as an entry in session_plan.monitoring, with the \
trigger captured in `threshold` or `action_if_present` and the required action captured in `action` or \
`action_if_present`.
- Each step should be one discrete, coach-actionable instruction. Do not merge unrelated instructions into \
a single step.
- qa_rubric must contain one yes/no checkable question per constraint, monitoring item, and target in the \
session plan, phrased so a coordinator auditing a session recording can answer it "yes" or "no".
- Leave a field unset when it does not apply to a given step or monitoring item. Do not fabricate values \
to fill a field.
"""


def structure_protocol(protocol_text: str, model: str | None = None) -> ProtocolOutput:
    """Call Claude with a strict output schema and return a validated ProtocolOutput."""
    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=model or DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": protocol_text}],
        output_format=ProtocolOutput,
    )
    return response.parsed_output
