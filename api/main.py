"""Minimal FastAPI wrapper around the Phase 1-3 pipeline: paste protocol text in, get the
structured session plan, QA checklist, and any validation warnings back.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.render import render_coach_plan, render_qa_checklist
from src.structure import structure_protocol
from src.validate import validate_escalation_coverage

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"
SAMPLES_DIR = REPO_ROOT / "samples"

app = FastAPI(title="Protocol-to-Checklist Translator")


class StructureRequest(BaseModel):
    protocol_text: str
    model: Optional[str] = None


class StructureResponse(BaseModel):
    session_plan: dict
    qa_rubric: List[str]
    coach_markdown: str
    qa_markdown: str
    validation_issues: List[str]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/samples")
def list_samples() -> dict:
    """Bundled sample protocols, keyed by filename stem, so the demo page can offer a quick-load menu."""
    return {f.stem: f.read_text(encoding="utf-8") for f in sorted(SAMPLES_DIR.glob("*.txt"))}


@app.post("/structure", response_model=StructureResponse)
def structure(req: StructureRequest) -> StructureResponse:
    text = req.protocol_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="protocol_text must not be empty")

    try:
        result = structure_protocol(text, model=req.model)
    except Exception as exc:  # surface the LLM/auth error to the demo UI instead of a bare 500
        raise HTTPException(status_code=502, detail=f"Structuring failed: {exc}") from exc

    issues = validate_escalation_coverage(text, result)

    return StructureResponse(
        session_plan=result.session_plan.model_dump(),
        qa_rubric=result.qa_rubric,
        coach_markdown=render_coach_plan(result),
        qa_markdown=render_qa_checklist(result),
        validation_issues=[str(issue) for issue in issues],
    )
