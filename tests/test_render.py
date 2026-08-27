from src.render import render_coach_plan, render_qa_checklist
from src.schema import MonitoringItem, ProtocolOutput, SessionPlan, SessionStep


def _sample_output() -> ProtocolOutput:
    return ProtocolOutput(
        session_plan=SessionPlan(
            week=3,
            condition="Post-op right total knee replacement",
            steps=[
                SessionStep(step=1, activity="Stationary cycling warm-up", duration_min=10),
                SessionStep(
                    step=2,
                    activity="Resistance band work, quadriceps and hamstrings",
                    constraints="Avoid full weight-bearing lunges",
                    duration_min=20,
                ),
            ],
            monitoring=[
                MonitoringItem(
                    metric="Joint swelling",
                    action_if_present="Escalate to physician",
                ),
                MonitoringItem(
                    metric="Pain level",
                    threshold=">4/10",
                    action="Escalate to physician",
                ),
            ],
        ),
        qa_rubric=[
            "Did the coach avoid full weight-bearing lunges?",
            "Was joint swelling checked and logged?",
        ],
    )


def test_render_coach_plan_includes_all_steps_and_monitoring():
    md = render_coach_plan(_sample_output())
    assert "# Session Plan -- Post-op right total knee replacement" in md
    assert "Stationary cycling warm-up" in md
    assert "Avoid full weight-bearing lunges" in md
    assert "Joint swelling" in md
    assert "Escalate to physician" in md


def test_render_qa_checklist_includes_rubric_and_escalation_audit():
    md = render_qa_checklist(_sample_output())
    assert "- [ ] Did the coach avoid full weight-bearing lunges?" in md
    assert "- [ ] Was joint swelling checked and logged?" in md
    assert "Escalation criteria to audit" in md
    assert "Pain level" in md
