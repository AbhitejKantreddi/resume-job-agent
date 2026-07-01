"""The 6-node agent pipeline (Section 5 of the build spec), implemented as an
in-process orchestrator.

Each node updates a shared ``Run`` object so the API can stream live progress.
When no Groq key is configured the pipeline uses deterministic sample data so
the whole flow still runs for a demo.
"""
from __future__ import annotations

import json
from typing import Any

from . import mock_data
from .groq_client import GroqClient
from .prompts import (
    JOB_QUERY_TEMPLATE,
    NODE1_RESUME_PARSER,
    NODE2_SKILL_ROLE_ANALYZER,
    NODE3_JOB_POSTPROCESS,
    NODE4_SKILL_GAP,
    NODE5_RESUME_REWRITER,
    NODE6_COVER_LETTER,
)
from .tavily_client import TavilyClient

# (node_id, human-readable status label shown in the UI)
NODES: list[tuple[str, str]] = [
    ("resume_parser", "Reading resume…"),
    ("skill_analyzer", "Analyzing skills & target roles…"),
    ("job_search", "Searching live job postings…"),
    ("skill_gap", "Scoring skill gaps…"),
    ("resume_rewriter", "Rewriting resume for top match…"),
    ("cover_letter", "Writing tailored cover letter…"),
]


class AgentPipeline:
    def __init__(self) -> None:
        self.groq = GroqClient()
        self.tavily = TavilyClient()

    # --- individual nodes -------------------------------------------------
    def parse_resume(self, raw_text: str) -> dict[str, Any]:
        if not self.groq.enabled:
            return mock_data.mock_resume_json(raw_text)
        return self.groq.generate_json(NODE1_RESUME_PARSER, f"Resume text:\n{raw_text}")

    def analyze_skills(self, resume_json: dict[str, Any]) -> dict[str, Any]:
        if not self.groq.enabled:
            return mock_data.mock_analysis_json(resume_json)
        payload = json.dumps(
            {
                "skills": resume_json.get("skills", []),
                "experience": resume_json.get("experience", []),
            }
        )
        return self.groq.generate_json(NODE2_SKILL_ROLE_ANALYZER, payload)

    def search_jobs(self, analysis_json: dict[str, Any], location: str) -> dict[str, Any]:
        titles = (analysis_json.get("target_titles") or [])[:3]
        if not self.groq.enabled or not self.tavily.enabled:
            return mock_data.mock_jobs_json(titles, location)
        raw_results: list[dict[str, Any]] = []
        for title in titles:
            query = JOB_QUERY_TEMPLATE.format(target_title=title, location=location)
            try:
                raw_results.extend(self.tavily.search(query, max_results=5))
            except Exception:
                continue
        # Keep the payload well under Groq free-tier per-minute token limits.
        payload = json.dumps({"search_results": raw_results})[:14000]
        return self.groq.generate_json(NODE3_JOB_POSTPROCESS, payload)

    def skill_gap(self, resume_json: dict[str, Any], jobs_json: dict[str, Any]) -> dict[str, Any]:
        if not self.groq.enabled:
            return mock_data.mock_gap_json(resume_json, jobs_json)
        payload = json.dumps(
            {
                "candidate_skills": resume_json.get("skills", []),
                "jobs": jobs_json.get("jobs", []),
            }
        )
        return self.groq.generate_json(NODE4_SKILL_GAP, payload)

    def rewrite_resume(self, resume_json: dict[str, Any], gap_analysis_json: dict[str, Any]) -> dict[str, Any]:
        top = (gap_analysis_json.get("matches") or [{}])[0]
        if not self.groq.enabled:
            return mock_data.mock_rewrite_json(resume_json, top)
        payload = json.dumps({"resume": resume_json, "top_match": top})
        return self.groq.generate_json(NODE5_RESUME_REWRITER, payload)

    def cover_letter(
        self,
        resume_json: dict[str, Any],
        gap_analysis_json: dict[str, Any],
        tailored_summary: str,
    ) -> dict[str, Any]:
        top = (gap_analysis_json.get("matches") or [{}])[0]
        if not self.groq.enabled:
            return mock_data.mock_cover_letter_json(resume_json, top)
        payload = json.dumps(
            {"resume": resume_json, "top_match": top, "tailored_summary": tailored_summary}
        )
        return self.groq.generate_json(NODE6_COVER_LETTER, payload)

    # --- orchestration ----------------------------------------------------
    def run_sync(self, run) -> None:
        """Execute the full pipeline against a Run, updating state as it goes.

        Intended to run in a background thread (see main.run_agent).
        """
        try:
            run.set_node("resume_parser", "in_progress")
            resume_json = self.parse_resume(run.raw_text)
            run.set_result("resume_json", resume_json)
            run.set_node("resume_parser", "done")

            run.set_node("skill_analyzer", "in_progress")
            analysis_json = self.analyze_skills(resume_json)
            run.set_result("analysis_json", analysis_json)
            run.set_node("skill_analyzer", "done")

            run.set_node("job_search", "in_progress")
            jobs_json = self.search_jobs(analysis_json, run.location)
            run.set_result("jobs_json", jobs_json)
            run.set_node("job_search", "done")

            run.set_node("skill_gap", "in_progress")
            gap_analysis_json = self.skill_gap(resume_json, jobs_json)
            run.set_result("gap_analysis_json", gap_analysis_json)
            run.set_node("skill_gap", "done")

            run.set_node("resume_rewriter", "in_progress")
            rewritten_resume_json = self.rewrite_resume(resume_json, gap_analysis_json)
            run.set_result("rewritten_resume_json", rewritten_resume_json)
            run.set_node("resume_rewriter", "done")

            run.set_node("cover_letter", "in_progress")
            cover_letter_json = self.cover_letter(
                resume_json,
                gap_analysis_json,
                rewritten_resume_json.get("tailored_summary", ""),
            )
            run.set_result("cover_letter_json", cover_letter_json)
            run.set_node("cover_letter", "done")

            run.finish()
        except Exception as exc:  # noqa: BLE001 - surface any node failure to the client
            run.finish(error=f"{type(exc).__name__}: {exc}")


# Module-level singleton reused across requests.
pipeline = AgentPipeline()
