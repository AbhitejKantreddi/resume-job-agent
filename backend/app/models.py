"""Pydantic request/response models for the API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class UploadResumeResponse(BaseModel):
    resume_id: str
    raw_text: str


class RunAgentRequest(BaseModel):
    resume_id: str | None = None
    raw_text: str
    location: str | None = None


class RunAgentResponse(BaseModel):
    run_id: str


class RunStatusResponse(BaseModel):
    run_id: str
    current_node: str
    status: str
    steps: list[dict[str, Any]]


class RunResultResponse(BaseModel):
    run_id: str
    status: str
    resume_json: dict[str, Any] | None = None
    analysis_json: dict[str, Any] | None = None
    jobs_json: dict[str, Any] | None = None
    gap_analysis_json: dict[str, Any] | None = None
    rewritten_resume_json: dict[str, Any] | None = None
    cover_letter_json: dict[str, Any] | None = None
    error: str | None = None


class GeneratePdfRequest(BaseModel):
    kind: str  # "resume" | "cover_letter"
    resume_json: dict[str, Any] | None = None
    rewritten_resume_json: dict[str, Any] | None = None
    cover_letter_json: dict[str, Any] | None = None
