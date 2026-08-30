"""
pdf_parser.py
Extracts raw text from a resume PDF and parses out structured fields:
name, email, phone, skills, experience.
"""
import os
import re

import pdfplumber

from exceptions import InvalidFileFormatError, PDFExtractionError
from models import Candidate
from logger_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Master skill vocabulary used to detect skills anywhere in the resume text,
# not just inside a labelled "Skills" section (resumes are inconsistent).
# ---------------------------------------------------------------------------
MASTER_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "rust",
    "php", "ruby", "kotlin", "swift", "scala", "r", "matlab",
    # Web / Frontend
    "html", "html5", "css", "css3", "react", "react.js", "reactjs", "angular",
    "vue", "vue.js", "next.js", "nodejs", "node.js", "redux", "bootstrap",
    "tailwind", "jquery", "django", "flask", "fastapi", "spring", "spring boot",
    "express", "express.js", ".net", "asp.net",
    # Data / ML
    "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", "nosql",
    "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
    "keras", "machine learning", "deep learning", "data analysis",
    "data science", "nlp", "opencv", "matplotlib", "seaborn", "power bi",
    "tableau", "excel",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github",
    "gitlab", "ci/cd", "terraform", "ansible", "linux", "shell scripting",
    "devops",
    # Mobile
    "android", "ios", "flutter", "react native",
    # Other / general
    "rest api", "restful api", "graphql", "microservices", "agile", "scrum",
    "oop", "object oriented programming", "data structures", "algorithms",
    "system design", "unit testing", "pytest", "junit", "blockchain",
    "tkinter", "pyqt", "selenium", "api development", "json", "xml",
]

SECTION_HEADERS = [
    "experience", "work experience", "professional experience", "employment history",
    "education", "skills", "technical skills", "projects", "certifications",
    "achievements", "summary", "objective", "profile", "declaration",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,6}")
YEARS_EXP_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience)?", re.IGNORECASE
)


def _extract_text(pdf_path: str) -> str:
    try:
        text_chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)
        text = "\n".join(text_chunks).strip()
        if not text:
            raise PDFExtractionError(
                os.path.basename(pdf_path),
                "No selectable text found (the PDF may be a scanned image).",
            )
        return text
    except PDFExtractionError:
        raise
    except Exception as exc:  # corrupt / unreadable PDF
        raise PDFExtractionError(os.path.basename(pdf_path), str(exc)) from exc


def _extract_name(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    skip_words = {"resume", "curriculum vitae", "cv", "biodata", "profile"}
    for line in lines[:8]:
        low = line.lower()
        if any(w in low for w in skip_words):
            continue
        if EMAIL_RE.search(line) or "http" in low or re.search(r"\d{4,}", line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            return line.title() if line.isupper() else line
    return "Not Found"


def _extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else "Not Found"


def _extract_phone(text: str) -> str:
    for match in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 10 <= len(digits) <= 13:
            return match.group(0).strip()
    return "Not Found"


def _extract_section(text: str, header_names) -> str:
    """Grab the block of text following any of the given section headers,
    stopping at the next known section header."""
    lines = text.splitlines()
    lower_lines = [ln.strip().lower() for ln in lines]

    start_idx = None
    for i, ln in enumerate(lower_lines):
        cleaned = ln.strip(":-• ").strip()
        if cleaned in header_names:
            start_idx = i + 1
            break
    if start_idx is None:
        return ""

    collected = []
    for ln in lines[start_idx:]:
        stripped_low = ln.strip(":-• ").strip().lower()
        if stripped_low in SECTION_HEADERS and stripped_low not in header_names:
            break
        if ln.strip():
            collected.append(ln.strip())
    return "\n".join(collected)


def _extract_skills(text: str) -> list:
    found = set()
    lower_text = text.lower()

    # 1. Direct keyword scan across the whole resume
    for skill in MASTER_SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, lower_text):
            found.add(skill)

    # 2. Also parse a dedicated "Skills" section for anything comma/bullet separated
    skills_section = _extract_section(text, {"skills", "technical skills"})
    if skills_section:
        for chunk in re.split(r"[,\n•|/]", skills_section):
            chunk = chunk.strip(" -\t")
            if 1 < len(chunk) <= 30 and not chunk.lower().startswith(("proficient", "familiar")):
                found.add(chunk.lower())

    # normalize a few duplicates
    normalized = set()
    alias = {
        "reactjs": "react", "react.js": "react", "node.js": "nodejs",
        "sklearn": "scikit-learn", "html5": "html", "css3": "css",
    }
    for s in found:
        normalized.add(alias.get(s, s))

    return sorted(normalized)


def _extract_experience(text: str) -> str:
    years_match = YEARS_EXP_RE.search(text)
    if years_match:
        return f"{years_match.group(1)} years"

    exp_section = _extract_section(
        text, {"experience", "work experience", "professional experience", "employment history"}
    )
    if exp_section:
        first_line = exp_section.splitlines()[0][:80]
        return first_line + ("..." if len(exp_section) > 80 else "")

    return "Not Found"


def parse_resume(pdf_path: str) -> Candidate:
    """Main entry point: validate, extract text, parse fields, return a Candidate."""
    filename = os.path.basename(pdf_path)

    if not filename.lower().endswith(".pdf"):
        raise InvalidFileFormatError(filename)

    logger.info(f"Parsing resume: {filename}")
    text = _extract_text(pdf_path)

    candidate = Candidate(
        file_name=filename,
        name=_extract_name(text),
        email=_extract_email(text),
        phone=_extract_phone(text),
        skills=_extract_skills(text),
        experience=_extract_experience(text),
        raw_text=text,
    )
    logger.debug(f"Parsed candidate: {candidate.name} | skills={len(candidate.skills)}")
    return candidate