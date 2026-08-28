"""Structured output schema shared by the LLM call, the validator, and the renderers."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SessionStep(BaseModel):
    step: int
    activity: str
    constraints: Optional[str] = Field(
        default=None, description="Restriction or modification that applies to this activity, if any"
    )
    duration_min: Optional[int] = Field(default=None, description="Duration in minutes, if specified")
    frequency: Optional[str] = Field(
        default=None, description="How often this activity recurs, e.g. 'weekly' -- if specified"
    )
    target: Optional[str] = Field(
        default=None, description="A numeric or qualitative target for this activity, if specified"
    )


class MonitoringItem(BaseModel):
    metric: str
    threshold: Optional[str] = Field(default=None, description="Threshold value that triggers the action")
    action: Optional[str] = Field(default=None, description="What to do when the threshold is crossed")
    action_if_present: Optional[str] = Field(
        default=None, description="What to do if this metric is observed at all, when there is no numeric threshold"
    )


class SessionPlan(BaseModel):
    week: Optional[int] = Field(default=None, description="Week number of the program, if specified")
    condition: str
    steps: List[SessionStep]
    monitoring: List[MonitoringItem]


class ProtocolOutput(BaseModel):
    session_plan: SessionPlan
    qa_rubric: List[str]


def ollama_json_schema() -> dict:
    """A flat JSON schema (no $ref/$defs) mirroring ProtocolOutput, for Ollama's structured-output
    `format` parameter. Ollama's constrained decoding is built on llama.cpp's JSON-schema-to-grammar
    converter, which is most reliable against an inlined schema -- so this is written out by hand
    rather than derived from ProtocolOutput.model_json_schema() (which uses $defs/$ref). Every field
    is listed in `required` with a nullable type, matching how strict-schema modes represent an
    optional field: present, value nullable.
    """
    session_step = {
        "type": "object",
        "properties": {
            "step": {"type": "integer"},
            "activity": {"type": "string"},
            "constraints": {"type": ["string", "null"]},
            "duration_min": {"type": ["integer", "null"]},
            "frequency": {"type": ["string", "null"]},
            "target": {"type": ["string", "null"]},
        },
        "required": ["step", "activity", "constraints", "duration_min", "frequency", "target"],
        "additionalProperties": False,
    }
    monitoring_item = {
        "type": "object",
        "properties": {
            "metric": {"type": "string"},
            "threshold": {"type": ["string", "null"]},
            "action": {"type": ["string", "null"]},
            "action_if_present": {"type": ["string", "null"]},
        },
        "required": ["metric", "threshold", "action", "action_if_present"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "session_plan": {
                "type": "object",
                "properties": {
                    "week": {"type": ["integer", "null"]},
                    "condition": {"type": "string"},
                    "steps": {"type": "array", "items": session_step},
                    "monitoring": {"type": "array", "items": monitoring_item},
                },
                "required": ["week", "condition", "steps", "monitoring"],
                "additionalProperties": False,
            },
            "qa_rubric": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["session_plan", "qa_rubric"],
        "additionalProperties": False,
    }
