from typing import Any, Dict, List
from datetime import datetime, timedelta
import asyncio
from .base import BaseAgent
from ..config.settings import (
    ACTOR_IDS,
    JOB_SEARCH_CONFIG,
    INITIAL_SCORING_WEIGHTS
)
from ..models.schema import ResumeData

class JobScraperAgent(BaseAgent):
    def __init__(self, apify_client):
        super().__init__(apify_client)
        self.linkedin_search_actor = ACTOR_IDS["linkedin_jobs_search"]
        self.linkedin_detail_actor = ACTOR_IDS["linkedin_job_detail"]
        self.indeed_scraper = ACTOR_IDS["indeed_scraper"]

    def _get_system_prompt(self) -> str:
        return """
        Job Scraping Agent responsible for:
        1. Initial job search from multiple sources
        2. Preliminary filtering and scoring
        3. Detailed information gathering for promising matches
        """

    def _search_linkedin_jobs(self, search_params: Dict[str, Any]) -> List[Dict]:
        """Perform initial LinkedIn job search."""
        search_input = {
            "keywords": search_params["keywords"],
            "location": search_params["location"],
            "limit": JOB_SEARCH_CONFIG["initial_results_per_source"]
        }
        
        return self.run_actor(
            actor_id=self.linkedin_search_actor,
            input_data=search_input
        )

    def _search_indeed_jobs(self, search_params: Dict[str, Any]) -> List[Dict]:
        """Perform initial Indeed job search."""
        search_input = {
            "keyword": search_params["keywords"],
            "location": search_params["location"],
            "maxResults": JOB_SEARCH_CONFIG["initial_results_per_source"]
        }
        
        return self.run_actor(
            actor_id=self.indeed_scraper,
            input_data=search_input
        )

    def _calculate_initial_score(self, job: Dict, resume_data: ResumeData) -> float:
        """Calculate preliminary score for a job listing."""
        scores = {
            "title_match": self._score_title_match(job["title"], resume_data.desired_role),
            "location_match": self._score_location_match(job["location"], resume_data.location_preference),
            "company_relevance": self._score_company_relevance(job["company"], resume_data.industry_experience),
            "posting_date": self._score_posting_date(job.get("posted_date", datetime.now()))
        }
        
        return sum(
            scores[key] * INITIAL_SCORING_WEIGHTS[key]
            for key in INITIAL_SCORING_WEIGHTS
        )

    def _fetch_job_details(self, job_urls: List[str]) -> List[Dict]:
        """Fetch detailed information for promising job listings."""
        detailed_jobs = []
        for url in job_urls:
            if "linkedin.com" in url:
                job_details = self.run_actor(
                    actor_id=self.linkedin_detail_actor,
                    input_data={"url": url}
                )
                detailed_jobs.extend(job_details)
            # Add similar handling for Indeed URLs if needed
        
        return detailed_jobs

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the job search workflow."""
        resume_data = state["resume_data"]
        work_mode_preference = state["feedback"].get("work_mode_preference", "Any")
        
        # Prepare search parameters
        search_params = {
            "keywords": resume_data.desired_role,
            "location": resume_data.location_preference
        }
        
        # Add work mode to keywords if specified
        if work_mode_preference and work_mode_preference != "Any":
            search_params["keywords"] += f" {work_mode_preference}"
        
        # Initial job search from multiple sources
        linkedin_jobs = self._search_linkedin_jobs(search_params)
        indeed_jobs = self._search_indeed_jobs(search_params)
        
        # Combine and score initial results
        all_jobs = []
        for job in linkedin_jobs + indeed_jobs:
            # Normalize job data structure
            normalized_job = self._normalize_job_data(job)
            
            # Calculate initial score
            score = self._calculate_initial_score(normalized_job, resume_data)
            normalized_job["initial_score"] = score
            all_jobs.append(normalized_job)
        
        # Sort by score and filter
        promising_jobs = sorted(
            [j for j in all_jobs if j["initial_score"] >= JOB_SEARCH_CONFIG["detail_fetch_threshold"]],
            key=lambda x: x["initial_score"],
            reverse=True
        )[:JOB_SEARCH_CONFIG["max_details_to_fetch"]]
        
        # Fetch detailed information for promising jobs
        job_urls = [job["url"] for job in promising_jobs if "url" in job]
        detailed_jobs = self._fetch_job_details(job_urls)
        
        # If we couldn't get detailed jobs, use the promising jobs
        if not detailed_jobs:
            detailed_jobs = promising_jobs
        
        # Update state
        state["jobs_scraped"] = True
        state["job_listings"] = detailed_jobs
        
        return state

    def _normalize_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job data from different sources to a common format."""
        normalized = {
            "job_id": job.get("id", job.get("jobId", str(hash(str(job))))),
            "title": job.get("title", job.get("name", "Unknown Position")),
            "company": job.get("company", job.get("companyName", "Unknown Company")),
            "location": job.get("location", job.get("place", "Unknown Location")),
            "url": job.get("url", job.get("link", job.get("applicationLink", ""))),
            "source": "LinkedIn" if "linkedin" in job.get("url", "") else "Indeed"
        }
        
        # Handle posted date
        posted_date = job.get("postedDate", job.get("date", job.get("listedAt", None)))
        if isinstance(posted_date, str):
            try:
                normalized["posted_date"] = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                normalized["posted_date"] = datetime.now() - timedelta(days=7)  # Default to 1 week ago
        else:
            normalized["posted_date"] = datetime.now() - timedelta(days=7)
        
        return normalized

    def _score_title_match(self, job_title: str, desired_role: str) -> float:
        """Score how well the job title matches the desired role."""
        # Implement fuzzy matching or keyword matching logic
        job_title = job_title.lower()
        desired_role = desired_role.lower()
        
        if job_title == desired_role:
            return 1.0
        elif desired_role in job_title or job_title in desired_role:
            return 0.8
        # Add more sophisticated matching logic here
        return 0.4

    def _score_location_match(self, job_location: str, preferred_location: str) -> float:
        """Score how well the job location matches preferences."""
        # Implement location matching logic
        if not job_location or not preferred_location:
            return 0.5
            
        job_location = job_location.lower()
        preferred_location = preferred_location.lower()
        
        if "remote" in job_location:
            return 1.0
        elif preferred_location in job_location:
            return 1.0
        # Add more sophisticated location matching logic here
        return 0.5

    def _score_company_relevance(self, company: str, industry_experience: List[str]) -> float:
        """Score company relevance based on industry experience."""
        # Implement company/industry matching logic
        # This could be enhanced with company industry data
        return 0.7  # Default score, improve with better matching logic

    def _score_posting_date(self, posted_date: datetime) -> float:
        """Score job based on how recently it was posted."""
        days_old = (datetime.now() - posted_date).days
        if days_old <= 7:
            return 1.0
        elif days_old <= 14:
            return 0.8
        elif days_old <= 21:
            return 0.6
        else:
            return 0.4