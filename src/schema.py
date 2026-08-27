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
