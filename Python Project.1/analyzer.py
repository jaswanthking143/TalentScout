from typing import Dict, Any
import pandas as pd
from utils import get_logger

logger = get_logger(__name__)


def normalize_series(s: pd.Series) -> pd.Series:
    if s.max() == s.min():
        return pd.Series(1.0, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


class Analyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def compute_base_scores(self) -> pd.DataFrame:
        df = self.df
        # Ensure numeric columns exist
        for col in ["avg_performance_score", "years_experience", "achievement_impact", "projects_delivered", "on_time_rate"]:
            if col not in df.columns:
                df[col] = 0.0

        # Normalize numeric indicators
        df["norm_perf"] = normalize_series(df["avg_performance_score"])
        df["norm_experience"] = normalize_series(df["years_experience"])
        df["norm_achievements"] = normalize_series(df["achievement_impact"])
        df["norm_projects"] = normalize_series(df["projects_delivered"])
        df["norm_on_time"] = normalize_series(df["on_time_rate"])

        logger.debug("Computed normalized indicators")
        return df

    def detect_high_performers(self, df_with_scores: pd.DataFrame, threshold: float = 0.8):
        # Simple high performer detection via weighted sum threshold
        if "suitability_score" not in df_with_scores.columns:
            raise ValueError("DataFrame must contain 'suitability_score'")
        high = df_with_scores[df_with_scores["suitability_score"] >= threshold].copy()
        logger.info("Detected %d high performers with threshold %s", len(high), threshold)
        return high