"""Protocol text -> structured session plan + QA rubric, via a schema-constrained LLM call.

Two providers, selected by the LLM_PROVIDER env var:
- "anthropic" (default) -- Claude API, via client.messages.parse against the Pydantic schema.
- "ollama" -- a local model through Ollama's structured-output `format` parameter. Free, no API
  key, but needs Ollama installed and running locally (see README).
"""

from __future__ import annotations

import json
import os

import anthropic
import requests

from .schema import ProtocolOutput, ollama_json_schema

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

ANTHROPIC_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

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
- Leave a field unset (null) when it does not apply to a given step or monitoring item. Do not fabricate \
values to fill a field.
- Respond with JSON only, matching the given schema exactly. No prose before or after the JSON.
"""


def _structure_with_anthropic(protocol_text: str, model: str | None) -> ProtocolOutput:
    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=model or ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": protocol_text}],
        output_format=ProtocolOutput,
    )
    return response.parsed_output


def _structure_with_ollama(protocol_text: str, model: str | None) -> ProtocolOutput:
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model or OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": protocol_text},
                ],
                "format": ollama_json_schema(),
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=180,
        )
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_HOST}. Is it running? Start it with `ollama serve` "
            f"(or just open the Ollama app), and make sure the model is pulled: "
            f"`ollama pull {model or OLLAMA_MODEL}`."
        ) from exc

    response.raise_for_status()
    content = response.json()["message"]["content"]
    return ProtocolOutput.model_validate(json.loads(content))


def structure_protocol(protocol_text: str, model: str | None = None) -> ProtocolOutput:
    """Call the configured LLM provider with a strict output schema and return a validated
    ProtocolOutput.
    """
    if LLM_PROVIDER == "ollama":
        return _structure_with_ollama(protocol_text, model)
    return _structure_with_anthropic(protocol_text, model)
