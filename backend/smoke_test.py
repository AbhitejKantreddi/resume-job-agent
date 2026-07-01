"""End-to-end smoke test for the backend (runs in MOCK mode, no API keys needed)."""
import io
import time

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_sample_resume_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    lines = [
        "Abhitej Kantreddi",
        "abhitejkantreddi@gmail.com | +91 90000 00000",
        "Skills: Python, FastAPI, Next.js, TypeScript, React, SQL",
        "Experience: Software Engineering Intern, Acme Labs (Summer 2025)",
        "- Built REST APIs in FastAPI serving 10k requests/day",
        "Education: B.Tech Computer Science, IIT Example, 2026",
    ]
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


def main():
    print("1) health:", client.get("/").json())

    pdf = make_sample_resume_pdf()
    up = client.post("/api/upload-resume", files={"file": ("resume.pdf", pdf, "application/pdf")})
    assert up.status_code == 200, up.text
    resume_id = up.json()["resume_id"]
    raw_text = up.json()["raw_text"]
    print(f"2) upload-resume OK: resume_id={resume_id}, extracted {len(raw_text)} chars")
    assert "Abhitej" in raw_text, "pdfplumber extraction failed"

    run = client.post("/api/run-agent", json={"resume_id": resume_id, "raw_text": raw_text, "location": "Remote"})
    assert run.status_code == 200, run.text
    run_id = run.json()["run_id"]
    print(f"3) run-agent OK: run_id={run_id}")

    # poll status
    for _ in range(50):
        st = client.get(f"/api/run-status/{run_id}").json()
        if st["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)
    print(f"4) run-status: {st['status']}; steps=" + ", ".join(f"{s['node']}:{s['status']}" for s in st["steps"]))
    assert st["status"] == "completed", st

    res = client.get(f"/api/run-result/{run_id}").json()
    for key in ("resume_json", "analysis_json", "jobs_json", "gap_analysis_json", "rewritten_resume_json", "cover_letter_json"):
        assert res.get(key), f"missing {key}"
    top = res["gap_analysis_json"]["matches"][0]
    print(f"5) run-result OK: {len(res['jobs_json']['jobs'])} jobs; top match {top['company']} @ {top['match_score']}%")

    r_pdf = client.post("/api/generate-pdf", json={"kind": "resume", "rewritten_resume_json": res["rewritten_resume_json"], "resume_json": res["resume_json"]})
    assert r_pdf.status_code == 200 and r_pdf.content[:4] == b"%PDF", "resume PDF failed"
    c_pdf = client.post("/api/generate-pdf", json={"kind": "cover_letter", "cover_letter_json": res["cover_letter_json"], "resume_json": res["resume_json"]})
    assert c_pdf.status_code == 200 and c_pdf.content[:4] == b"%PDF", "cover letter PDF failed"
    print(f"6) generate-pdf OK: resume={len(r_pdf.content)} bytes, cover_letter={len(c_pdf.content)} bytes")

    # save sample PDFs so we can eyeball them
    with open("sample_tailored_resume.pdf", "wb") as f:
        f.write(r_pdf.content)
    with open("sample_cover_letter.pdf", "wb") as f:
        f.write(c_pdf.content)

    print("\nALL CHECKS PASSED ✅ (mock mode)")


if __name__ == "__main__":
    main()
