# Protocol-to-Checklist Translator

A doctor writes a protocol in plain language. A coach in a different city has to execute it
identically, every session, without the doctor in the room. This tool closes that gap: paste an
unstructured clinical protocol in, get a coach-facing session plan and a coordinator-facing QA
checklist out -- generated from the same structured source, with a built-in safety check that
catches an LLM silently dropping a red-flag instruction.

## Why this exists

Praan Health runs physician-led chronic care programs across 25+ conditions, delivered by a
distributed team of doctors, nutritionists, strength coaches, and care coordinators in multiple
cities. Praan's own job posting names this exact translation problem:

> "Work closely with doctors, nutritionists, and strength coaches to translate clinical protocols
> into simple, intuitive software experiences."

The bottleneck isn't writing a good protocol -- it's making sure every coach, in every city,
executes that protocol consistently. Today that translation from "doctor's clinical notes" to
"what the coach actually does in a session" is presumably manual and doesn't scale as the team
hires more coaches. This is a working prototype of the tool that would close that gap.

## Example

**Input** (unstructured protocol text):

```
Post-op right total knee replacement, week 3 post-surgery. Light resistance band work only,
2 sets of 12 reps, no more than 20 minutes. Avoid full weight-bearing lunges and deep squats
past 90 degrees until week 6. Watch for joint swelling or pain above 4/10 -- if present, stop
the session and escalate to the physician same day. Protein target 1.2g/kg bodyweight. Reassess
range of motion weekly.
```

**Output**: a structured JSON session plan + QA rubric ([src/schema.py](src/schema.py)), rendered
into two documents from that single source of truth ([src/render.py](src/render.py)):

- **Coach session plan** -- steps, durations, constraints, and what to watch for.
- **Coordinator QA checklist** -- a yes/no checklist per constraint, target, and monitoring item,
  plus an explicit escalation-criteria audit table.

Try it against four hand-written sample protocols in [samples/](samples/) -- post-op orthopedic
recovery, diabetes management, hypertension/lifestyle, and post-MI cardiac rehab -- chosen to be
different enough that the prompt has to generalize, not pattern-match one example.

## The validation layer -- why it's not optional

For a healthcare-adjacent tool, an LLM silently dropping an instruction like "escalate to
physician if pain > 4/10" isn't a formatting bug, it's a safety issue. So structuring the protocol
isn't the last step -- [src/validate.py](src/validate.py) keyword-matches every escalation /
red-flag sentence in the *source* protocol text and checks that it's reflected somewhere in the
structured `monitoring` output. Anything the LLM dropped gets flagged, in the CLI and in the web
UI, before it ever reaches a coach.

This check runs entirely offline (no LLM call, no network) and is proven with a deliberately
broken test case, not just a happy path: [tests/test_validate.py](tests/test_validate.py) builds
one correct output and asserts the validator passes it, then strips the escalation entries out of
the *same* output and asserts the validator catches it.

```bash
python -m pytest
```

## Architecture

```
protocol text
      |
      v
[structure.py]   schema-constrained LLM call (Claude, or a local model via Ollama -- see below)
      |
      v
[validate.py]    every escalation phrase in the input must appear in the output monitoring section
      |
      v
[render.py]      same JSON -> coach session plan (markdown) + coordinator QA checklist (markdown)
      |
      +--> src/cli.py   (CLI: file in, JSON/markdown out)
      +--> api/main.py  (FastAPI: paste text in a browser, see both outputs + warnings)
```

## Running it

Two interchangeable LLM providers, selected by `LLM_PROVIDER` in `.env` -- [src/structure.py](src/structure.py)
routes between them, everything downstream (`validate.py`, `render.py`, the CLI, the web UI) is
identical either way.

```bash
pip install -r requirements.txt
cp .env.example .env
```

**Option A -- Ollama (local, free, no API key):**

```bash
# install from https://ollama.com/download, then:
ollama pull llama3.1
# .env: LLM_PROVIDER=ollama   (this is the default in .env.example)
```

Structured output is enforced via Ollama's schema-constrained `format` parameter
([src/schema.py](src/schema.py) `ollama_json_schema()`), the local equivalent of Claude's
`client.messages.parse`. Quality is lower than Claude on the same prompt -- expect this path to
need more scrutiny of its output, which is exactly what the validation layer is there to catch.

**Option B -- Anthropic Claude API:**

```bash
# .env: LLM_PROVIDER=anthropic, ANTHROPIC_API_KEY=...
```

**CLI:**

```bash
python -m src.cli samples/01_post_op_knee.txt                   # structured JSON to stdout
python -m src.cli samples/01_post_op_knee.txt --render          # + both markdown docs to stdout
python -m src.cli samples/01_post_op_knee.txt --out-dir out/    # + write markdown files
```

**Web:**

```bash
uvicorn api.main:app --reload
# open http://127.0.0.1:8000, load a sample or paste your own protocol text
```

**Tests:**

```bash
python -m pytest
```

## What this deliberately doesn't do

This is a credible prototype, not a production system -- scope was kept tight on purpose:

- No auth, no database, no multi-tenant support -- it's stateless by design.
- No attempt to handle every possible protocol format -- 4 realistic, well-chosen samples beat
  infinite edge cases for proving the approach generalizes.
- No visual design polish on the web UI -- plain and functional, so the time went into the
  structuring prompt and the validation layer instead.

## Project structure

```
src/
  schema.py     structured output schema (Pydantic) shared by every layer
  structure.py  protocol text -> ProtocolOutput, via a schema-constrained call to Claude or Ollama
  validate.py   escalation-coverage cross-check (source text vs. structured output)
  render.py     ProtocolOutput -> coach markdown + QA markdown
  cli.py        CLI entrypoint
api/main.py     FastAPI wrapper (GET /, GET /samples, POST /structure)
web/index.html  single-page frontend, no build step, no external dependencies
samples/        4 hand-written sample protocols
tests/          validation + rendering tests, including a deliberately-triggered failure case
```
