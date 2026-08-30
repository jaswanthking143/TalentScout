import os
import json
import pandas as pd
from typing import Dict, Any
from utils import get_logger

logger = get_logger(__name__)


def ensure_output_dir(path: str):
    os.makedirs(path, exist_ok=True)


def generate_report(df: pd.DataFrame, role_name: str, required_skills: list, out_dir: str = "output") -> Dict[str, Any]:
    ensure_output_dir(out_dir)
    # Prepare summary
    top = df.head(10)
    report = {
        "role": role_name,
        "required_skills": required_skills,
        "candidate_count": int(len(df)),
        "top_candidates": []
    }
    for _, row in top.iterrows():
        report["top_candidates"].append({
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "suitability_score": float(row["suitability_score"]),
            "skill_match": float(row["skill_match"]),
            "avg_performance_score": float(row["avg_performance_score"]),
            "years_experience": float(row["years_experience"]),
            "achievement_impact": float(row["achievement_impact"])
        })
    # Save JSON and CSV
    json_path = os.path.join(out_dir, "report.json")
    csv_path = os.path.join(out_dir, "report.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    # Save full DataFrame
    df_out = df.copy()
    df_out.to_csv(csv_path, index=False)
    logger.info("Saved report to %s and %s", json_path, csv_path)
    return {"json": json_path, "csv": csv_path, "summary": report}