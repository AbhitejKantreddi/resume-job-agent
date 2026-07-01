"""PDF text extraction (pdfplumber) and PDF generation (reportlab)."""
from __future__ import annotations

import html
import io
import re
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def extract_text(file_bytes: bytes) -> str:
    """Extract plain text from a PDF using pdfplumber."""
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def _rich(text: str) -> str:
    """Escape HTML then convert **bold** markdown to <b> tags for reportlab."""
    escaped = html.escape(text or "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ResName", fontSize=18, leading=22, spaceAfter=2, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="ResContact", fontSize=9, leading=12, textColor=colors.HexColor("#555555"), spaceAfter=12))
    styles.add(ParagraphStyle(name="ResHead", fontSize=12, leading=15, spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a1a")))
    styles.add(ParagraphStyle(name="ResBody", fontSize=10, leading=14))
    styles.add(ParagraphStyle(name="ResBullet", fontSize=10, leading=14, leftIndent=12, bulletIndent=2, spaceAfter=4))
    return styles


def build_resume_pdf(rewritten_resume_json: dict[str, Any], resume_json: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch)
    s = _styles()
    story: list[Any] = []

    name = resume_json.get("name") or "Your Name"
    contact = " | ".join(x for x in [resume_json.get("email", ""), resume_json.get("phone", "")] if x)
    story.append(Paragraph(_rich(name), s["ResName"]))
    if contact:
        story.append(Paragraph(_rich(contact), s["ResContact"]))

    summary = rewritten_resume_json.get("tailored_summary", "")
    if summary:
        story.append(Paragraph("Professional Summary", s["ResHead"]))
        story.append(Paragraph(_rich(summary), s["ResBody"]))

    bullets = rewritten_resume_json.get("tailored_bullets", [])
    if bullets:
        story.append(Paragraph("Experience Highlights (Tailored)", s["ResHead"]))
        for b in bullets:
            improved = b.get("improved") or b.get("original") or ""
            story.append(Paragraph("• " + _rich(improved), s["ResBullet"]))

    skills = resume_json.get("skills", [])
    if skills:
        story.append(Paragraph("Skills", s["ResHead"]))
        story.append(Paragraph(_rich(", ".join(skills)), s["ResBody"]))

    experience = resume_json.get("experience", [])
    if experience:
        story.append(Paragraph("Experience", s["ResHead"]))
        for exp in experience:
            header = " — ".join(x for x in [exp.get("title", ""), exp.get("company", "")] if x)
            dur = exp.get("duration", "")
            line = f"<b>{html.escape(header)}</b>" + (f"  ({html.escape(dur)})" if dur else "")
            story.append(Paragraph(line, s["ResBody"]))
            for h in exp.get("highlights", []):
                story.append(Paragraph("• " + _rich(h), s["ResBullet"]))
            story.append(Spacer(1, 4))

    doc.build(story)
    return buf.getvalue()


def build_cover_letter_pdf(cover_letter_json: dict[str, Any], resume_json: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                            leftMargin=1.0 * inch, rightMargin=1.0 * inch)
    s = _styles()
    story: list[Any] = []

    name = resume_json.get("name") or "Your Name"
    contact = " | ".join(x for x in [resume_json.get("email", ""), resume_json.get("phone", "")] if x)
    story.append(Paragraph(_rich(name), s["ResName"]))
    if contact:
        story.append(Paragraph(_rich(contact), s["ResContact"]))
    story.append(Paragraph(date.today().strftime("%B %d, %Y"), s["ResBody"]))
    story.append(Spacer(1, 12))

    body = cover_letter_json.get("cover_letter", "")
    for para in [p for p in body.split("\n\n") if p.strip()]:
        story.append(Paragraph(_rich(para).replace("\n", "<br/>"), s["ResBody"]))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()
