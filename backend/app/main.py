"""FastAPI backend for the Agentic Resume & Job-Match Assistant.

Endpoints (Section 6 of the build spec):
  POST /api/upload-resume     -> extract text from an uploaded PDF
  POST /api/run-agent         -> start the 6-node pipeline, returns run_id
  GET  /api/run-stream/{id}   -> Server-Sent Events stream of live node status
  GET  /api/run-status/{id}   -> current node status (polling alternative)
  GET  /api/run-result/{id}   -> final JSON results for every node
  POST /api/generate-pdf      -> render a tailored resume or cover letter PDF
"""
from __future__ import annotations

import asyncio
import io
import json
import threading
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import pdf_utils
from .agent.pipeline import pipeline
from .config import get_settings
from .models import (
    GeneratePdfRequest,
    RunAgentRequest,
    RunAgentResponse,
    RunResultResponse,
    RunStatusResponse,
    UploadResumeResponse,
)
from .store import store

settings = get_settings()
app = FastAPI(title="Agentic Resume & Job-Match Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Naive in-memory storage for uploaded resume text (swap for Supabase to persist).
_resumes: dict[str, str] = {}


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "resume-job-agent",
        "mock_mode": settings.mock_mode,
        "groq": settings.groq_enabled,
        "tavily": settings.tavily_enabled,
    }


@app.post("/api/upload-resume", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    is_pdf = file.content_type == "application/pdf" or (file.filename or "").lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    data = await file.read()
    try:
        raw_text = pdf_utils.extract_text(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}")
    if not raw_text:
        raise HTTPException(status_code=422, detail="No text found in the PDF (is it a scanned image?).")
    resume_id = uuid.uuid4().hex[:12]
    _resumes[resume_id] = raw_text
    return UploadResumeResponse(resume_id=resume_id, raw_text=raw_text)


@app.post("/api/run-agent", response_model=RunAgentResponse)
def run_agent(body: RunAgentRequest):
    raw_text = body.raw_text or _resumes.get(body.resume_id or "", "")
    if not raw_text:
        raise HTTPException(status_code=400, detail="raw_text is required (or a known resume_id).")
    location = body.location or settings.default_location
    run = store.create(raw_text=raw_text, location=location)
    threading.Thread(target=pipeline.run_sync, args=(run,), daemon=True).start()
    return RunAgentResponse(run_id=run.run_id)


@app.get("/api/run-status/{run_id}", response_model=RunStatusResponse)
def run_status(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Unknown run_id")
    snap = run.snapshot()
    return RunStatusResponse(
        run_id=run_id,
        current_node=snap["current_node"],
        status=snap["status"],
        steps=snap["steps"],
    )


@app.get("/api/run-result/{run_id}", response_model=RunResultResponse)
def run_result(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Unknown run_id")
    snap = run.snapshot()
    r = snap["results"]
    return RunResultResponse(
        run_id=run_id,
        status=snap["status"],
        resume_json=r.get("resume_json"),
        analysis_json=r.get("analysis_json"),
        jobs_json=r.get("jobs_json"),
        gap_analysis_json=r.get("gap_analysis_json"),
        rewritten_resume_json=r.get("rewritten_resume_json"),
        cover_letter_json=r.get("cover_letter_json"),
        error=snap["error"],
    )


@app.get("/api/run-stream/{run_id}")
async def run_stream(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Unknown run_id")

    async def event_gen():
        last_version = -1
        while True:
            snap = run.snapshot()
            if snap["version"] != last_version:
                last_version = snap["version"]
                payload = {
                    "run_id": run_id,
                    "status": snap["status"],
                    "current_node": snap["current_node"],
                    "steps": snap["steps"],
                }
                yield f"data: {json.dumps(payload)}\n\n"
            if snap["status"] in ("completed", "failed"):
                yield f"event: done\ndata: {json.dumps({'status': snap['status']})}\n\n"
                break
            await asyncio.sleep(0.4)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/generate-pdf")
def generate_pdf(body: GeneratePdfRequest):
    if body.kind == "resume":
        if not body.rewritten_resume_json:
            raise HTTPException(status_code=400, detail="rewritten_resume_json required for kind=resume")
        pdf_bytes = pdf_utils.build_resume_pdf(body.rewritten_resume_json, body.resume_json or {})
        filename = "tailored_resume.pdf"
    elif body.kind == "cover_letter":
        if not body.cover_letter_json:
            raise HTTPException(status_code=400, detail="cover_letter_json required for kind=cover_letter")
        pdf_bytes = pdf_utils.build_cover_letter_pdf(body.cover_letter_json, body.resume_json or {})
        filename = "cover_letter.pdf"
    else:
        raise HTTPException(status_code=400, detail="kind must be 'resume' or 'cover_letter'")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
