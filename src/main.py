"""
AI Job Search Agent - Apify Actor

This actor analyzes a resume and finds matching job opportunities from LinkedIn and Indeed.
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime
from apify import Actor
from apify.consts import ActorEventTypes
from openai import OpenAI

# Import settings
from config.settings import (
    OPENAI_MODEL,
    ACTOR_IDS,
    FINAL_SCORING_WEIGHTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Event names and prices
EVENTS = {
    'resume_parse': 0.10,      # Resume parsing
    'job_score': 0.02,         # Per job scoring
    'results_summary': 0.10    # Final summary
}

# Define output schema
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "object",
            "properties": {
                "resumeSummary": {"type": "object"},
                "searchParameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "workMode": {"type": "string"}
                    }
                }
            }
        },
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "position": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "matchScore": {"type": "number"},
                    "matchDetails": {"type": "object"},
                    "applicationUrl": {"type": "string"},
                    "source": {"type": "string"}
                }
            }
        },
        "statistics": {
            "type": "object",
            "properties": {
                "totalJobsFound": {"type": "integer"},
                "averageMatchScore": {"type": "number"},
                "topSkillsRequested": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "timestamp": {"type": "string"}
            }
        }
    }
}

class JobSearchWorkflow:
    """Main workflow class for job search process."""
    
    def __init__(self, apify_client):
        self.client = apify_client
        self.JOBS_PER_SOURCE = 10  # Fixed number of jobs per source
        self.openai_client = None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete job search workflow."""
        try:
            # Initialize OpenAI client with API key from input
            self.openai_client = OpenAI(api_key=input_data["openAiApiKey"])
            
            # Initialize Apify client with token from input
            self.client.token = input_data["apifyApiToken"]
            
            state = {
                "resume_text": input_data["resumeText"],
                "location_preference": input_data.get("locationPreference", ""),
                "work_mode_preference": input_data.get("workModePreference", "Any"),
                "search_radius": input_data.get("searchRadius", 25),
                "min_salary": input_data.get("minSalary", 0),
                "resume_info": {},
                "jobs": [],
                "scored_jobs": [],
                "results": {}
            }
            
            # Execute workflow steps
            state = await self.extract_resume_info(state)
            state = await self.search_jobs(state)
            state = await self.score_jobs(state)
            state = await self.format_results(state)
            
            return state["results"]
            
        except Exception as e:
            logger.error(f"Error in workflow: {str(e)}")
            raise
    
    async def extract_resume_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from the resume using OpenAI."""
        try:
            logger.info("Extracting resume information...")
            resume_text = state["resume_text"]
            
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a resume parser. Extract the following information from the resume: desired role, skills, years of experience, education, and location preference. Format your response as JSON."
                    },
                    {
                        "role": "user",
                        "content": f"Parse this resume:\n\n{resume_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            resume_info = json.loads(response.choices[0].message.content)
            resume_info["work_mode_preference"] = state["work_mode_preference"]
            
            state["resume_info"] = resume_info
            logger.info(f"Extracted resume information: {resume_info}")
            
            # Charge for resume parsing
            await Actor.push_data({
                "type": "charge",
                "eventName": "resume_parse"
            })
            
            return state
        except Exception as e:
            logger.error(f"Error extracting resume info: {str(e)}")
            raise
    
    async def search_jobs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search for jobs on LinkedIn and Indeed."""
        try:
            logger.info("Starting job search process...")
            resume_info = state["resume_info"]
            
            # Prepare search parameters
            desired_role = resume_info.get("desired_role", "Software Engineer")
            simplified_role = desired_role.split("|")[0].strip() if "|" in desired_role else desired_role
            location = state["location_preference"] or resume_info.get("location_preference", "")
            
            search_params = {
                "keywords": simplified_role.lower(),
                "location": location
            }
            
            logger.info(f"Search parameters: {json.dumps(search_params, indent=2)}")
            
            # Combined jobs list
            all_jobs = []
            
            # Search LinkedIn with shorter timeout
            logger.info("Initiating LinkedIn job search...")
            linkedin_run_input = {
                "keywords": search_params["keywords"],
                "location": "United States",
                "page_number": 1,
                "sort": "relevant",
                "experienceLevel": "mid_senior",
                "limit": self.JOBS_PER_SOURCE
            }
            
            linkedin_jobs = []
            try:
                linkedin_run = await self.client.actor(ACTOR_IDS["linkedin_jobs_search"]).call(
                    run_input=linkedin_run_input,
                    timeout_secs=60,  # Reduced timeout
                    memory_mbytes=256,
                    build="latest"
                )
                
                logger.info(f"LinkedIn actor run ID: {linkedin_run.get('id')}")
                
                try:
                    linkedin_dataset = await self.client.dataset(linkedin_run["defaultDatasetId"]).list_items()
                    linkedin_jobs_raw = linkedin_dataset.items if linkedin_dataset.items else []
                    linkedin_jobs = linkedin_jobs_raw[:self.JOBS_PER_SOURCE]
                    
                    if linkedin_jobs:
                        sample_job = linkedin_jobs[0]
                        logger.info(f"Sample LinkedIn job: {sample_job.get('title')} at {sample_job.get('company')}")
                except Exception as e:
                    logger.error(f"Error processing LinkedIn dataset: {str(e)}")
            except Exception as e:
                logger.error(f"LinkedIn search failed: {str(e)}")
            
            all_jobs.extend(linkedin_jobs)
            
            # Search Indeed with optimized parameters
            logger.info("Initiating Indeed job search...")
            indeed_run_input = {
                "position": search_params["keywords"],
                "country": "US",
                "location": search_params["location"],
                "maxItems": self.JOBS_PER_SOURCE,  # Limit max items
                "parseCompanyDetails": False,  # Skip company details to speed up
                "saveOnlyUniqueItems": True,
                "followApplyRedirects": False,  # Skip redirects to speed up
                "maxConcurrency": 5  # Limit concurrency to avoid blocks
            }
            
            indeed_jobs = []
            try:
                indeed_run = await self.client.actor(ACTOR_IDS["indeed_scraper"]).call(
                    run_input=indeed_run_input,
                    timeout_secs=60,  # Reduced timeout
                    memory_mbytes=512,
                    build="latest"
                )
                
                logger.info(f"Indeed actor run ID: {indeed_run.get('id')}")
                
                try:
                    indeed_dataset = await self.client.dataset(indeed_run["defaultDatasetId"]).list_items()
                    indeed_jobs_raw = indeed_dataset.items if indeed_dataset.items else []
                    
                    # Process Indeed jobs with limit
                    indeed_jobs = []
                    for job in indeed_jobs_raw[:self.JOBS_PER_SOURCE]:  # Apply limit here
                        standardized_job = self.standardize_indeed_job(job)
                        if standardized_job:
                            indeed_jobs.append(standardized_job)
                            if len(indeed_jobs) >= self.JOBS_PER_SOURCE:
                                break
                    
                    if indeed_jobs:
                        sample_job = indeed_jobs[0]
                        logger.info(f"Sample Indeed job: {sample_job.get('title')} at {sample_job.get('company')}")
                except Exception as e:
                    logger.error(f"Error processing Indeed dataset: {str(e)}")
            except Exception as e:
                logger.error(f"Indeed search failed: {str(e)}")
            
            all_jobs.extend(indeed_jobs)
            
            # Standardize all jobs with limit
            standardized_jobs = []
            for job in all_jobs:
                if len(standardized_jobs) >= self.JOBS_PER_SOURCE * 2:
                    break
                standardized_job = self.standardize_job_data(job)
                if standardized_job:
                    standardized_jobs.append(standardized_job)
            
            logger.info(f"Total standardized jobs ready for processing: {len(standardized_jobs)}")
            state["jobs"] = standardized_jobs
            return state
        except Exception as e:
            logger.error(f"Error in search_jobs: {str(e)}")
            state["jobs"] = []
            return state
    
    def standardize_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize job data structure."""
        try:
            standardized = {
                "title": job.get("title") or job.get("positionName") or job.get("name", ""),
                "company": job.get("company") or job.get("companyName", ""),
                "location": job.get("location") or job.get("place", ""),
                "description": job.get("description") or job.get("jobDescription", ""),
                "url": job.get("url") or job.get("applicationLink", ""),
                "source": "LinkedIn" if "linkedin.com" in job.get("url", "") else "Indeed"
            }
            
            # Skip jobs with missing essential data
            if not standardized["title"] or not standardized["company"]:
                return None
            
            return standardized
        except Exception as e:
            logger.error(f"Error standardizing job data: {str(e)}")
            return None
    
    def standardize_indeed_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize Indeed job data."""
        try:
            standardized = {
                "title": job.get("positionName", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "description": job.get("description", ""),
                "url": job.get("applicationLink", ""),
                "source": "Indeed"
            }
            
            # Add company description if available
            if job.get("companyInfo") and job.get("companyInfo").get("companyDescription"):
                if not standardized["description"]:
                    standardized["description"] = job["companyInfo"]["companyDescription"]
            
            # Skip jobs with missing essential data
            if not standardized["title"] or not standardized["company"]:
                return None
            
            return standardized
        except Exception as e:
            logger.error(f"Error standardizing Indeed job: {str(e)}")
            return None
    
    async def score_jobs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Score jobs based on resume match."""
        try:
            logger.info("Scoring jobs...")
            jobs = state["jobs"]
            resume_info = state["resume_info"]
            
            scored_jobs = []
            
            for job in jobs:
                job_description = job.get("description", "") or job.get("jobDescription", "")
                job_title = job.get("title", "") or job.get("name", "")
                job_location = job.get("location", "") or job.get("place", "")
                company = job.get("company", "") or job.get("companyName", "")
                
                # Prepare the prompt for the LLM
                prompt = f"""
                Score how well this job matches the candidate's profile:
                
                JOB:
                Title: {job_title}
                Company: {company}
                Location: {job_location}
                Description: {job_description[:1000]}...
                
                CANDIDATE:
                Desired Role: {resume_info.get('desired_role', 'Software Engineer')}
                Skills: {', '.join(resume_info.get('skills', []))}
                Experience: {resume_info.get('years_experience', 'Not specified')} years
                Location Preference: {resume_info.get('location_preference', '')}
                Work Mode Preference: {state["work_mode_preference"]}
                
                Score each category from 0-100:
                1. Skills Match: How well the candidate's skills match the job requirements
                2. Experience Match: How well the candidate's experience level matches the job
                3. Location Match: How well the job location matches the candidate's preference
                4. Company/Role Fit: Overall fit with the company and role
                
                Provide a total score and explanation for each category.
                Format your response as JSON with the following structure:
                {{
                    "skills_match": {{"score": 85, "explanation": "Explanation text here"}},
                    "experience_match": {{"score": 75, "explanation": "Explanation text here"}},
                    "location_match": {{"score": 90, "explanation": "Explanation text here"}},
                    "company_fit": {{"score": 80, "explanation": "Explanation text here"}},
                    "total_score": 82.5
                }}
                """
                
                response = self.openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a job matching assistant that evaluates how well jobs match a candidate's profile."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                try:
                    scores = json.loads(response.choices[0].message.content)
                    
                    # Ensure total_score is a number
                    if "total_score" not in scores or not isinstance(scores["total_score"], (int, float)):
                        # Calculate total score if missing or invalid
                        weights = FINAL_SCORING_WEIGHTS
                        total_score = 0
                        if "skills_match" in scores and isinstance(scores["skills_match"], dict) and "score" in scores["skills_match"]:
                            total_score += scores["skills_match"]["score"] * weights.get("skills_match", 0.3)
                        if "experience_match" in scores and isinstance(scores["experience_match"], dict) and "score" in scores["experience_match"]:
                            total_score += scores["experience_match"]["score"] * weights.get("experience_match", 0.25)
                        if "location_match" in scores and isinstance(scores["location_match"], dict) and "score" in scores["location_match"]:
                            total_score += scores["location_match"]["score"] * weights.get("location_match", 0.25)
                        if "company_fit" in scores and isinstance(scores["company_fit"], dict) and "score" in scores["company_fit"]:
                            total_score += scores["company_fit"]["score"] * weights.get("company_fit", 0.2)
                        
                        scores["total_score"] = total_score
                    
                    # Add the scores to the job data
                    scored_job = job.copy()
                    scored_job["match_score"] = scores
                    scored_job["total_score"] = scores.get("total_score", 0)
                    
                    scored_jobs.append(scored_job)
                    logger.info(f"Scored job: {job_title} at {company} - Score: {scored_job['total_score']}")
                    
                    # Charge for job scoring
                    await Actor.push_data({
                        "type": "charge",
                        "eventName": "job_score"
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing score response: {str(e)}")
                    # Add a basic score
                    scored_job = job.copy()
                    scored_job["match_score"] = {
                        "skills_match": {"score": 70, "explanation": "Basic score due to error in detailed scoring."},
                        "experience_match": {"score": 70, "explanation": "Basic score due to error in detailed scoring."},
                        "location_match": {"score": 70, "explanation": "Basic score due to error in detailed scoring."},
                        "company_fit": {"score": 70, "explanation": "Basic score due to error in detailed scoring."},
                        "total_score": 70,
                        "explanation": "Basic score due to error in detailed scoring."
                    }
                    scored_job["total_score"] = 70
                    scored_jobs.append(scored_job)
                    logger.info(f"Applied default score to job: {job_title} at {company} - Score: 70 (due to error)")
            
            # Sort by score
            scored_jobs.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            state["scored_jobs"] = scored_jobs
            
            logger.info(f"Scored {len(scored_jobs)} jobs")
            return state
        except Exception as e:
            logger.error(f"Error scoring jobs: {str(e)}")
            state["scored_jobs"] = []
            return state
    
    async def format_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format the final results for output."""
        try:
            logger.info("Formatting results...")
            scored_jobs = state["scored_jobs"]
            resume_info = state["resume_info"]
            
            # Calculate statistics
            total_jobs = len(scored_jobs)
            avg_score = sum(job.get("total_score", 0) for job in scored_jobs) / total_jobs if total_jobs > 0 else 0
            
            # Extract top skills requested
            all_skills = []
            for job in scored_jobs:
                description = job.get("description", "") or job.get("jobDescription", "")
                if description:
                    # Use a simple approach to extract skills from the description
                    common_skills = ["Python", "JavaScript", "Java", "C++", "React", "Angular", "Node.js", 
                                   "AWS", "Azure", "SQL", "NoSQL", "Docker", "Kubernetes", "Machine Learning"]
                    for skill in common_skills:
                        if skill.lower() in description.lower() and skill not in all_skills:
                            all_skills.append(skill)
            
            # Format the results
            results = {
                "query": {
                    "resumeSummary": resume_info,
                    "searchParameters": {
                        "location": state["location_preference"] or resume_info.get("location_preference", ""),
                        "workMode": state["work_mode_preference"]
                    }
                },
                "results": [
                    {
                        "position": job.get("title", "") or job.get("name", ""),
                        "company": job.get("company", "") or job.get("companyName", ""),
                        "location": job.get("location", "") or job.get("place", ""),
                        "matchScore": job.get("total_score", 0),
                        "matchDetails": job.get("match_score", {}),
                        "applicationUrl": (
                            job.get("applyUrl", "") or  # LinkedIn format
                            job.get("applicationUrl", "") or  # Another LinkedIn format
                            job.get("apply_url", "") or  # Indeed format
                            job.get("url", "") or  # Generic fallback
                            job.get("link", "") or  # Another generic fallback
                            ""
                        ),
                        "source": "LinkedIn" if any(x in str(job.get("url", "")) for x in ["linkedin.com", "lnkd.in"]) else "Indeed"
                    }
                    for job in scored_jobs[:10]  # Limit to top 10 jobs
                ],
                "statistics": {
                    "totalJobsFound": total_jobs,
                    "averageMatchScore": round(avg_score, 1),
                    "topSkillsRequested": all_skills[:5],  # Top 5 skills
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            state["results"] = results
            
            # Charge for results summary
            await Actor.push_data({
                "type": "charge",
                "eventName": "results_summary"
            })
            
            logger.info("Results formatted successfully")
            return state
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            state["results"] = {
                "query": {"resumeSummary": state["resume_info"]},
                "results": [],
                "statistics": {"totalJobsFound": 0, "timestamp": datetime.now().isoformat()}
            }
            return state

def validate_input(input_data: Dict[str, Any]) -> None:
    """Validate actor input parameters."""
    if not input_data.get("apifyApiToken"):
        raise ValueError("Apify API token is required")
    if not input_data.get("openAiApiKey"):
        raise ValueError("OpenAI API key is required")
    if not input_data.get("resumeText"):
        raise ValueError("Resume text is required")

async def main():
    async with Actor:
        try:
            # Set output schema
            await Actor.set_value('OUTPUT_SCHEMA', OUTPUT_SCHEMA)
            
            # Get and validate input
            actor_input = await Actor.get_input() or {}
            validate_input(actor_input)
            
            # Initialize and run workflow
            workflow = JobSearchWorkflow(Actor.apify_client)
            results = await workflow.run(actor_input)
            
            # Push results to dataset
            await Actor.push_data(results)
            
            logger.info("Job search completed successfully")
            
        except Exception as e:
            logger.error(f"Actor failed: {str(e)}")
            raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())