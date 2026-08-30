"""
analyzer.py
Scores each parsed Candidate against a role entered by the HR user and
ranks them by how well their skills match that role's requirements.
"""
from typing import List

from models import Candidate
from exceptions import NoCandidateDataError, EmptyRoleInputError
from logger_config import get_logger

logger = get_logger(__name__)

# Predefined skill requirements for common roles. Matching is fuzzy: if the
# typed role isn't an exact key, we fall back to the closest partial match,
# and if nothing matches at all we derive keywords from the role text itself.
ROLE_SKILLS = {
    "python developer": ["python", "django", "flask", "fastapi", "sql", "git", "oop", "rest api"],
    "python full stack developer": [
        "python", "django", "flask", "react", "javascript", "html", "css",
        "sql", "mysql", "git", "rest api",
    ],
    "full stack developer": [
        "javascript", "react", "nodejs", "express", "html", "css", "sql",
        "mongodb", "git", "rest api",
    ],
    "frontend developer": ["html", "css", "javascript", "react", "angular", "vue", "bootstrap", "tailwind"],
    "backend developer": ["python", "java", "nodejs", "sql", "mongodb", "rest api", "microservices", "git"],
    "java developer": ["java", "spring", "spring boot", "sql", "oop", "git", "rest api"],
    "data scientist": [
        "python", "pandas", "numpy", "machine learning", "deep learning",
        "scikit-learn", "tensorflow", "sql", "data analysis", "matplotlib",
    ],
    "data analyst": ["sql", "excel", "power bi", "tableau", "python", "pandas", "data analysis"],
    "machine learning engineer": [
        "python", "machine learning", "deep learning", "tensorflow", "pytorch",
        "scikit-learn", "numpy", "pandas",
    ],
    "devops engineer": ["docker", "kubernetes", "aws", "azure", "jenkins", "ci/cd", "linux", "terraform", "git"],
    "android developer": ["android", "java", "kotlin", "sql", "git"],
    "react developer": ["react", "javascript", "html", "css", "redux", "rest api", "git"],
    "software engineer": ["python", "java", "javascript", "sql", "git", "data structures", "algorithms", "oop"],
    "cloud engineer": ["aws", "azure", "gcp", "docker", "kubernetes", "linux", "terraform"],
}


def _resolve_role_skills(role: str) -> list:
    role_key = role.strip().lower()

    if role_key in ROLE_SKILLS:
        return ROLE_SKILLS[role_key]

    # partial / fuzzy match against known role names
    best_match, best_overlap = None, 0
    role_words = set(role_key.split())
    for known_role, skills in ROLE_SKILLS.items():
        known_words = set(known_role.split())
        overlap = len(role_words & known_words)
        if overlap > best_overlap:
            best_match, best_overlap = known_role, overlap
    if best_match:
        logger.info(f"Role '{role}' fuzzy-matched to '{best_match}'")
        return ROLE_SKILLS[best_match]

    # last resort: treat meaningful words typed by the HR user as the
    # required "skills" themselves (e.g. a role we've never seen before)
    stopwords = {"developer", "engineer", "role", "position", "candidate", "with", "for", "and"}
    fallback = [w for w in role_key.split() if w not in stopwords and len(w) > 2]
    logger.info(f"Role '{role}' unrecognized; using fallback keywords {fallback}")
    return fallback


def analyze_candidates(candidates: List[Candidate], role: str) -> List[Candidate]:
    """Scores and sorts candidates (descending) against the given role.
    Mutates and returns the same Candidate objects with match_score,
    matched_skills, and missing_skills populated."""
    if not candidates:
        raise NoCandidateDataError()
    if not role or not role.strip():
        raise EmptyRoleInputError()

    required_skills = set(_resolve_role_skills(role))
    if not required_skills:
        required_skills = {role.strip().lower()}

    for c in candidates:
        candidate_skills = set(c.skills)
        matched = sorted(candidate_skills & required_skills)
        missing = sorted(required_skills - candidate_skills)
        score = (len(matched) / len(required_skills)) * 100 if required_skills else 0.0

        c.matched_skills = matched
        c.missing_skills = missing
        c.match_score = round(score, 1)

    ranked = sorted(candidates, key=lambda c: c.match_score, reverse=True)
    logger.info(f"Analyzed {len(ranked)} candidates for role '{role}'")
    return ranked