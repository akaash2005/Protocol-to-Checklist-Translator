"""Proves the validation layer both passes good output and catches a dropped escalation
criterion. Run with: python -m pytest
"""

from pathlib import Path

from src.schema import MonitoringItem, ProtocolOutput, SessionPlan, SessionStep
from src.validate import validate_escalation_coverage

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


def _knee_protocol_text() -> str:
    return (SAMPLES_DIR / "01_post_op_knee.txt").read_text(encoding="utf-8")


def _knee_output_with_escalation() -> ProtocolOutput:
    return ProtocolOutput(
        session_plan=SessionPlan(
            week=3,
            condition="Post-op right total knee replacement",
            steps=[
                SessionStep(step=1, activity="Stationary cycling warm-up", duration_min=10),
                SessionStep(
                    step=2,
                    activity="Resistance band work, quadriceps and hamstrings",
                    constraints="2 sets of 12 reps, avoid full weight-bearing lunges and deep squats past 90 degrees",
                    duration_min=20,
                ),
            ],
            monitoring=[
                MonitoringItem(
                    metric="Joint swelling, redness, or warmth around the incision",
                    action_if_present="Stop the session and escalate to the physician same day",
                ),
                MonitoringItem(
                    metric="Pain during or after exercise",
                    threshold="above 4/10",
                    action_if_present="Stop the session and escalate to the physician same day",
                ),
            ],
        ),
        qa_rubric=[
            "Did the coach avoid full weight-bearing lunges and deep squats past 90 degrees?",
            "Was joint swelling, redness, or warmth checked and logged?",
            "Was pain level checked, and escalated to the physician if above 4/10?",
        ],
    )


def _knee_output_missing_escalation() -> ProtocolOutput:
    """Same as above but with the swelling/pain escalation criterion dropped entirely --
    the failure mode the validator exists to catch.
    """
    good = _knee_output_with_escalation()
    good.session_plan.monitoring = []
    return good


def test_validation_passes_when_escalation_is_present():
    issues = validate_escalation_coverage(_knee_protocol_text(), _knee_output_with_escalation())
    assert issues == []


def test_validation_catches_dropped_escalation_criterion():
    issues = validate_escalation_coverage(_knee_protocol_text(), _knee_output_missing_escalation())
    assert len(issues) == 1
    assert "escalate" in issues[0].escalation_sentence.lower()
    assert "physician" in issues[0].missing_keywords or "escalate" in issues[0].missing_keywords
