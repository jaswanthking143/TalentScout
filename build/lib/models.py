"""
models.py
Candidate dataclass shared across the parser, analyzer, and GUI.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Candidate:
    file_name: str
    name: str = "Not Found"
    email: str = "Not Found"
    phone: str = "Not Found"
    skills: List[str] = field(default_factory=list)
    experience: str = "Not Found"
    raw_text: str = ""

    # populated only after "Analyze" is run
    match_score: Optional[float] = None
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)

    def skills_display(self, limit: int = 6) -> str:
        if not self.skills:
            return "Not Found"
        shown = self.skills[:limit]
        text = ", ".join(shown)
        if len(self.skills) > limit:
            text += f"  (+{len(self.skills) - limit} more)"
        return text

    def to_dict(self) -> dict:
        return asdict(self)