# TrendScout — Data-driven Talent Discovery & Performance Analysis

TrendScout analyzes candidate/employee performance data to discover high-potential talent for roles and opportunities. It uses structured performance metrics, skills, experience, and achievements to compute suitability scores and recommendations.

Features included:
- Candidate and employee profiles (JSON)
- Store skills and experience
- Record performance metrics and achievements
- Analyze achievements and compute normalized scores
- Compare and rank candidates for a role
- Recommend suitable candidates
- Generate JSON/CSV talent analysis report
- Logging and exception handling

Requirements
- Python 3.9+
- pandas

Quick start
1. Create a virtualenv and install dependencies:
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. Run the example:
   python main.py

3. Outputs:
   - output/report.json
   - output/report.csv
   - logs/trendscout.log

Project structure
- data/sample_candidates.json — sample dataset to start with
- trend_scout/ — implementation modules
- main.py — run the pipeline with example role
- output/ — generated reports

Extending
- Replace sample_candidates.json with your data source
- Add resume parsing or AI ranking in recommender.py
- Add persistence (database) or REST API wrapper
