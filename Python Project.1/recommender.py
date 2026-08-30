from typing import Dict, Any, List
import pandas as pd
from analyzer import Analyzer
from utils import get_logger

logger = get_logger(__name__)


def skill_match_score(candidate_skills: List[str], required_skills: List[str]) -> float:
    if not required_skills:
        return 1.0
    cand = set(s.lower() for s in candidate_skills)
    req = set(s.lower() for s in required_skills)
    matched = cand.intersection(req)
    return len(matched) / len(req)


class Recommender:
    def __init__(self, df: pd.DataFrame, weights: Dict[str, float] = None):
        self.df = df.copy()
        # default weights (sum doesn't need to be 1; scores will be normalized)
        self.weights = weights or {
            "skill_match": 0.4,
            "norm_perf": 0.25,
            "norm_experience": 0.15,
            "norm_achievements": 0.1,
            "norm_on_time": 0.1
        }

    def compute_suitability(self, required_skills: List[str]) -> pd.DataFrame:
        df = Analyzer(self.df).compute_base_scores()
        df["skill_match"] = df["skills"].apply(lambda s: skill_match_score(s, required_skills))
        # Weighted sum
        df["raw_suitability"] = (
            df["skill_match"] * self.weights.get("skill_match", 0) +
            df["norm_perf"] * self.weights.get("norm_perf", 0) +
            df["norm_experience"] * self.weights.get("norm_experience", 0) +
            df["norm_achievements"] * self.weights.get("norm_achievements", 0) +
            df["norm_on_time"] * self.weights.get("norm_on_time", 0)
        )
        # Normalize suitability to 0-1
        if df["raw_suitability"].max() == df["raw_suitability"].min():
            df["suitability_score"] = 1.0
        else:
            df["suitability_score"] = (df["raw_suitability"] - df["raw_suitability"].min()) / (df["raw_suitability"].max() - df["raw_suitability"].min())
        df = df.sort_values("suitability_score", ascending=False).reset_index(drop=True)
        logger.info("Computed suitability scores and ranked %d profiles", len(df))
        return df

    def top_k(self, df_with_scores: pd.DataFrame, k: int = 5):
        return df_with_scores.head(k)