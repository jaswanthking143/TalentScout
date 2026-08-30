import json
import os
from typing import List
import pandas as pd
from models import Profile
from utils import TrendScoutError, get_logger


logger = get_logger(__name__)


def load_profiles_from_json(path: str) -> List[Profile]:
    if not os.path.exists(path):
        logger.error("Data file not found: %s", path)
        raise TrendScoutError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    profiles = []
    for entry in data:
        try:
            profiles.append(Profile.from_dict(entry))
        except Exception as e:
            logger.exception("Failed to parse entry: %s", entry)
    logger.info("Loaded %d profiles from %s", len(profiles), path)
    return profiles


def profiles_to_dataframe(profiles: List[Profile]) -> pd.DataFrame:
    rows = []
    for p in profiles:
        avg_score = None
        scores = p.performance_metrics.get("scores") or []
        if scores:
            avg_score = sum(scores) / len(scores)
        achievement_impact = sum(a.get("impact_score", 0) for a in p.achievements)
        rows.append({
            "id": p.id,
            "type": p.type,
            "name": p.name,
            "years_experience": p.years_experience,
            "skills": p.skills,
            "avg_performance_score": avg_score if avg_score is not None else 0.0,
            "achievement_impact": achievement_impact,
            "projects_delivered": p.performance_metrics.get("kpIs", {}).get("projects_delivered", 0),
            "on_time_rate": p.performance_metrics.get("kpIs", {}).get("on_time_rate", 0.0),
            "certifications": p.certifications,
        })
    df = pd.DataFrame(rows)
    logger.debug("Converted profiles to DataFrame with shape %s", df.shape)
    return df