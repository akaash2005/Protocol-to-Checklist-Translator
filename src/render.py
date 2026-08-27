"""Structured JSON -> two markdown renderers, from the same source: a coach-facing session plan
and a coordinator-facing QA checklist.
"""

from __future__ import annotations

from .schema import ProtocolOutput


def render_coach_plan(output: ProtocolOutput) -> str:
    plan = output.session_plan
    lines = [f"# Session Plan -- {plan.condition}"]
    if plan.week is not None:
        lines.append(f"**Week:** {plan.week}")
    lines.append("")

    lines.append("## Steps")
    for step in plan.steps:
        lines.append(f"### {step.step}. {step.activity}")
        if step.duration_min is not None:
            lines.append(f"- Duration: {step.duration_min} min")
        if step.frequency:
            lines.append(f"- Frequency: {step.frequency}")
        if step.target:
            lines.append(f"- Target: {step.target}")
        if step.constraints:
            lines.append(f"- **Constraint:** {step.constraints}")
        lines.append("")

    if plan.monitoring:
        lines.append("## Watch for")
        for item in plan.monitoring:
            trigger = item.threshold or "if observed"
            action = item.action or item.action_if_present or "escalate to physician"
            lines.append(f"- **{item.metric}** ({trigger}) -> {action}")
        lines.append("")

    return "\n".join(lines)


def render_qa_checklist(output: ProtocolOutput) -> str:
    plan = output.session_plan
    lines = [f"# QA Checklist -- {plan.condition}"]
    if plan.week is not None:
        lines.append(f"**Week:** {plan.week}")
    lines.append("")

    lines.append("## Checklist")
    for item in output.qa_rubric:
        lines.append(f"- [ ] {item}")
    lines.append("")

    if plan.monitoring:
        lines.append("## Escalation criteria to audit")
        for item in plan.monitoring:
            trigger = item.threshold or "any occurrence"
            action = item.action or item.action_if_present or "escalate to physician"
            lines.append(f"- [ ] **{item.metric}** -- trigger: {trigger} -- required action: {action}")
        lines.append("")

    return "\n".join(lines)
