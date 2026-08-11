"""Example run for TrendScout pipeline"""

from data_loader import load_profiles_from_json, profiles_to_dataframe
from recommender import Recommender
from report import generate_report
from utils import get_logger

logger = get_logger(__name__)


def main():
    data_path = "sample_candidates.json"
    profiles = load_profiles_from_json(data_path)
    df = profiles_to_dataframe(profiles)

    # Example role definition (customize)
    role_name = "Senior Data Analyst"
    required_skills = ["python", "sql", "pandas"]

    # Optional: adjust weights for your hiring priorities
    weights = {
        "skill_match": 0.45,
        "norm_perf": 0.3,
        "norm_experience": 0.15,
        "norm_achievements": 0.05,
        "norm_on_time": 0.05
    }

    recommender = Recommender(df, weights=weights)
    scored = recommender.compute_suitability(required_skills)
    top = recommender.top_k(scored, k=5)

    logger.info("Top candidates for %s:", role_name)
    for idx, r in top.iterrows():
        logger.info("  %d. %s (id=%s) score=%.3f match=%.2f", idx+1, r["name"], r["id"], r["suitability_score"], r["skill_match"])

    # Detect high performers
    # We consider high performers those with suitability_score >= 0.8
    high_performers = scored[scored["suitability_score"] >= 0.8]
    logger.info("Found %d candidates with suitability >= 0.8", len(high_performers))

    # Generate final report
    out = generate_report(scored, role_name, required_skills, out_dir="output")
    logger.info("Generated report files: %s", out)


if __name__ == "__main__":
    main()