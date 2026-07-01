"""Deterministic sample outputs used when API keys are absent (MOCK mode).

This lets the full 6-step pipeline and the UI run end-to-end for a demo
without any API keys configured.
"""
from __future__ import annotations

from typing import Any


def mock_resume_json(raw_text: str) -> dict[str, Any]:
    return {
        "name": "Abhitej Kantreddi",
        "email": "abhitejkantreddi@gmail.com",
        "phone": "+91 90000 00000",
        "skills": ["Python", "FastAPI", "Next.js", "TypeScript", "React", "SQL", "REST APIs", "Git"],
        "experience": [
            {
                "company": "Acme Labs",
                "title": "Software Engineering Intern",
                "duration": "Summer 2025",
                "highlights": [
                    "Built REST APIs in FastAPI serving 10k requests/day",
                    "Automated data pipelines with Python",
                ],
            }
        ],
        "education": [
            {"institution": "IIT Example", "degree": "B.Tech, Computer Science", "year": "2026"}
        ],
        "projects": [
            {
                "name": "Agentic Resume Assistant",
                "description": "Multi-step AI agent that tailors resumes to live job postings",
                "tech": ["Python", "FastAPI", "Next.js", "Groq"],
            }
        ],
    }


def mock_analysis_json(resume_json: dict[str, Any]) -> dict[str, Any]:
    return {
        "top_skills": ["Python", "FastAPI", "Next.js", "TypeScript", "React"],
        "target_titles": [
            "Software Engineer Intern",
            "Backend Engineer Intern",
            "Full Stack Developer Intern",
        ],
        "seniority": "Intern",
    }


def mock_jobs_json(titles: list[str], location: str) -> dict[str, Any]:
    companies = ["Stripe", "Notion", "Vercel", "Datadog"]
    titles = titles or ["Software Engineer Intern"]
    jobs = []
    for i, title in enumerate(titles):
        company = companies[i % len(companies)]
        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "url": f"https://example.com/jobs/{company.lower()}-{i}",
                "key_requirements": ["Python", "REST APIs", "Cloud (AWS/GCP)", "Docker"],
            }
        )
    return {"jobs": jobs}


def mock_gap_json(resume_json: dict[str, Any], jobs_json: dict[str, Any]) -> dict[str, Any]:
    skills = {s.lower() for s in resume_json.get("skills", [])}
    matches = []
    for job in jobs_json.get("jobs", []):
        reqs = job.get("key_requirements", [])
        matching = [r for r in reqs if r.lower() in skills]
        missing = [r for r in reqs if r.lower() not in skills]
        score = int(60 + 40 * (len(matching) / max(len(reqs), 1)))
        matches.append(
            {
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                "match_score": score,
                "missing_skills": missing,
                "matching_skills": matching,
            }
        )
    matches.sort(key=lambda m: m["match_score"], reverse=True)
    return {"matches": matches}


def mock_rewrite_json(resume_json: dict[str, Any], top_match: dict[str, Any]) -> dict[str, Any]:
    company = top_match.get("company", "the target company")
    return {
        "tailored_summary": (
            f"Computer Science student and builder targeting a role at **{company}**, with hands-on "
            f"experience shipping **Python** and **FastAPI** backends and **Next.js** frontends."
        ),
        "tailored_bullets": [
            {
                "original": "Built REST APIs in FastAPI serving 10k requests/day",
                "improved": "Designed and shipped **REST APIs** in **FastAPI** serving 10k requests/day, with automated tests and CI.",
            },
            {
                "original": "Automated data pipelines with Python",
                "improved": "Automated data pipelines in **Python**, cutting manual processing time by 70%.",
            },
        ],
    }


def mock_cover_letter_json(resume_json: dict[str, Any], top_match: dict[str, Any]) -> dict[str, Any]:
    name = resume_json.get("name", "the candidate")
    company = top_match.get("company", "your team")
    role = top_match.get("job_title", "the role")
    return {
        "cover_letter": (
            f"Dear Hiring Team at {company},\n\n"
            f"I'm excited to apply for the {role} position. As a computer science student who has shipped "
            f"FastAPI backends serving thousands of requests a day, I care about building reliable systems "
            f"that real users depend on.\n\n"
            f"In a recent internship I built REST APIs and automated Python data pipelines end to end — the "
            f"same full-stack ownership {company} is looking for. I move fast, write tested code, and enjoy "
            f"turning ambiguous problems into shipped features.\n\n"
            f"I'd welcome the chance to bring that energy to {company}. Thank you for your time and "
            f"consideration.\n\nSincerely,\n{name}"
        )
    }
