# Protocol-to-Checklist Translator

Turns an unstructured clinical protocol (written by a doctor, nutritionist, or strength coach) into a
structured, step-by-step session plan and a QA rubric, so a newly hired coach in any city can execute
it consistently, without the doctor in the room.

Status: Phase 2 of 5 (validation layer). See the build plan below as later phases land.

## Phase 1 -- core structuring pipeline

A CLI that takes a protocol text file in and prints structured JSON out, via a schema-constrained call
to the Claude API (`client.messages.parse` with a Pydantic output schema in [src/schema.py](src/schema.py)).

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

### Run

```bash
python -m src.cli samples/01_post_op_knee.txt
```

Four hand-written sample protocols live in [samples/](samples/), covering post-op orthopedic recovery,
diabetes management, hypertension/lifestyle, and post-MI cardiac rehab -- different enough to exercise
the structuring prompt beyond a single condition.

## Phase 2 -- validation layer

For a healthcare-adjacent tool, an LLM silently dropping an escalation criterion (e.g. "escalate to
physician if pain > 4/10") is a safety issue, not a formatting bug. [src/validate.py](src/validate.py)
keyword-matches every escalation / red-flag sentence in the source protocol and checks that it's
reflected somewhere in the structured `monitoring` section of the output; anything that isn't gets
flagged. This runs entirely offline (no LLM call), so it's fast and independently testable.

The CLI now runs this check automatically after structuring and prints any flagged criteria to stderr.

[tests/test_validate.py](tests/test_validate.py) proves the check actually catches something: one test
asserts a complete output passes, the other deliberately strips the escalation entries out of the same
output and asserts the validator flags it.

```bash
python -m pytest
```

## Planned phases

- Phase 3 -- rendering layer: coach-facing session plan + coordinator-facing QA checklist.
- Phase 4 -- minimal FastAPI + single-page web wrapper.
- Phase 5 -- README polish tying this back to Praan Health's stated need.
