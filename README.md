# Protocol-to-Checklist Translator

Turns an unstructured clinical protocol (written by a doctor, nutritionist, or strength coach) into a
structured, step-by-step session plan and a QA rubric, so a newly hired coach in any city can execute
it consistently, without the doctor in the room.

Status: Phase 1 of 5 (core structuring pipeline). See the build plan below as later phases land.

## Phase 1 -- core structuring pipeline (this phase)

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

## Planned phases

- Phase 2 -- validation layer: every escalation/red-flag phrase in the input must appear in the output.
- Phase 3 -- rendering layer: coach-facing session plan + coordinator-facing QA checklist.
- Phase 4 -- minimal FastAPI + single-page web wrapper.
- Phase 5 -- README polish tying this back to Praan Health's stated need.
