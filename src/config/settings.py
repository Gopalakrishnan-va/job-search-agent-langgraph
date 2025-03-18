import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys - these should be set as environment variables
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Model Configuration
OPENAI_MODEL = "gpt-4o-mini"  # Using the cheapest model for testing

# Apify Actor IDs
ACTOR_IDS: Dict[str, str] = {
    "linkedin_jobs_search": "apimaestro/linkedin-jobs-scraper-api",
    "linkedin_job_detail": "apimaestro/linkedin-job-detail",
    "indeed_scraper": "misceres/indeed-scraper"
}

# Job Search Settings
JOB_SEARCH_CONFIG = {
    "initial_results_per_source": 5,    # Reduced for testing
    "detail_fetch_threshold": 0.6,      # Minimum initial score to fetch details
    "max_details_to_fetch": 5,          # Reduced for testing
    "max_days_old": 30                  # Maximum age of job postings
}

# Scoring weights for initial filtering
INITIAL_SCORING_WEIGHTS = {
    "title_match": 0.4,
    "location_match": 0.3,
    "company_relevance": 0.2,
    "posting_date": 0.1
}

# Detailed scoring weights
FINAL_SCORING_WEIGHTS = {
    "skills_match": 0.40,
    "experience_match": 0.25,
    "location_match": 0.20,
    "company_fit": 0.15
}

# System settings
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds