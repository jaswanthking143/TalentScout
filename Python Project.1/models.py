from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Profile:
    id: str
    type: str  # 'candidate' or 'employee'
    name: str
    years_experience: float
    skills: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    achievements: List[Dict[str, Any]] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Profile":
        return cls(
            id=d.get("id"),
            type=d.get("type", "candidate"),
            name=d.get("name"),
            years_experience=float(d.get("years_experience", 0)),
            skills=[s.lower() for s in d.get("skills", [])],
            performance_metrics=d.get("performance_metrics", {}),
            achievements=d.get("achievements", []),
            certifications=d.get("certifications", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "years_experience": self.years_experience,
            "skills": self.skills,
            "performance_metrics": self.performance_metrics,
            "achievements": self.achievements,
            "certifications": self.certifications,
        }