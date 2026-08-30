"""
main.py
Entry point for TalentScout — Resume Intake & Role-Fit Analyzer.

Run:
    python main.py
"""
from logger_config import get_logger
from gui import launch_app

logger = get_logger("Main")


def main():
    logger.info("Starting TalentScout application...")
    try:
        launch_app()
    except Exception:
        logger.exception("TalentScout crashed unexpectedly.")
        raise
    finally:
        logger.info("TalentScout closed.")


if __name__ == "__main__":
    main()