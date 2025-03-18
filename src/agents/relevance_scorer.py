from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from .base import BaseAgent
from ..config.settings import OPENAI_API_KEY, OPENAI_MODEL, FINAL_SCORING_WEIGHTS

class RelevanceScorerAgent(BaseAgent):
    def __init__(self, apify_client):
        super().__init__(apify_client)
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.2
        )

    def _get_system_prompt(self) -> str:
        return """
        You are a Relevance Scorer Agent responsible for:
        1. Analyzing job details against resume
        2. Calculating match scores
        3. Ranking job opportunities
        
        For each job, you will calculate scores in these categories:
        - Position Match (25%): How well the job title matches the desired role
        - Skills & Experience (30%): Match between required skills and candidate's skills
        - Location (15%): Match between job location and candidate's preference
        - Company Match (15%): Fit with company culture, size, industry
        - Salary Match (10%): If salary info is available, how well it matches expectations
        - Benefits (5%): Quality of benefits package
        
        For each category, provide:
        1. A score from 0-100
        2. A brief explanation of the score
        
        Return a JSON object with the total score, score breakdown, and match details.
        """

    def _score_job(self, job: Dict[str, Any], resume_data: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Score a job listing against resume data using LLM."""
        # Prepare the input for the LLM
        job_json = json.dumps(job, default=str)
        resume_json = json.dumps(resume_data, default=str)
        preferences_json = json.dumps(preferences, default=str)
        
        prompt = f"""
        Score this job opportunity against the candidate's resume and preferences.
        
        JOB DETAILS:
        {job_json}
        
        RESUME DATA:
        {resume_json}
        
        PREFERENCES:
        {preferences_json}
        
        Calculate scores for each category and provide explanations.
        Return your analysis as a JSON object with these fields:
        - total_score: Overall match percentage (0-100)
        - score_breakdown: Object with scores for each category
        - match_details: Object with explanations for each category
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Extract JSON from response
        try:
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            # Fallback to manual scoring if LLM fails
            return self._manual_score_job(job, resume_data, preferences)

    def _manual_score_job(self, job: Dict[str, Any], resume_data: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Manual scoring method as fallback."""
        # Basic scoring logic
        position_match = self._score_position_match(job.get("title", ""), resume_data.get("desired_role", ""))
        skills_match = self._score_skills_match(
            job.get("required_skills", []), 
            resume_data.get("skills", [])
        )
        location_match = self._score_location_match(
            job.get("location", ""), 
            resume_data.get("location_preference", ""),
            preferences.get("work_mode_preference", "Any")
        )
        company_match = 70  # Default value
        salary_match = 65  # Default value
        benefits_match = 60  # Default value
        
        # Calculate weighted score
        total_score = (
            position_match * FINAL_SCORING_WEIGHTS["position_match"] +
            skills_match * FINAL_SCORING_WEIGHTS["skills_experience"] +
            location_match * FINAL_SCORING_WEIGHTS["location"] +
            company_match * FINAL_SCORING_WEIGHTS["company_match"] +
            salary_match * FINAL_SCORING_WEIGHTS["salary_match"] +
            benefits_match * FINAL_SCORING_WEIGHTS["benefits"]
        ) * 100
        
        return {
            "total_score": round(total_score, 1),
            "score_breakdown": {
                "position_match": position_match * 100,
                "skills_experience": skills_match * 100,
                "location": location_match * 100,
                "company_match": company_match,
                "salary_match": salary_match,
                "benefits": benefits_match
            },
            "match_details": {
                "position_match": f"The job title '{job.get('title', '')}' is a {position_match*100:.0f}% match with desired role '{resume_data.get('desired_role', '')}'",
                "skills_experience": f"Matched {skills_match*100:.0f}% of required skills",
                "location": f"Location match: {location_match*100:.0f}%",
                "company_match": "Company appears to be a reasonable match",
                "salary_match": "Salary information limited",
                "benefits": "Benefits information limited"
            }
        }

    def _score_position_match(self, job_title: str, desired_role: str) -> float:
        """Score position match between job title and desired role."""
        if not job_title or not desired_role:
            return 0.5
            
        job_title = job_title.lower()
        desired_role = desired_role.lower()
        
        if job_title == desired_role:
            return 1.0
        elif desired_role in job_title:
            return 0.9
        elif job_title in desired_role:
            return 0.8
        
        # Check for common words
        job_words = set(job_title.split())
        role_words = set(desired_role.split())
        common_words = job_words.intersection(role_words)
        
        if common_words:
            return 0.7 * (len(common_words) / max(len(job_words), len(role_words)))
        
        return 0.4  # Default score for low match

    def _score_skills_match(self, required_skills: List[str], candidate_skills: List[str]) -> float:
        """Score skills match between required skills and candidate skills."""
        if not required_skills:
            return 0.7  # Default if no required skills specified
        
        if not candidate_skills:
            return 0.3  # Low score if candidate has no skills listed
        
        # Normalize skills to lowercase for comparison
        required_lower = [skill.lower() for skill in required_skills]
        candidate_lower = [skill.lower() for skill in candidate_skills]
        
        # Count matches
        matches = sum(1 for skill in required_lower if any(
            candidate_skill in skill or skill in candidate_skill 
            for candidate_skill in candidate_lower
        ))
        
        return min(1.0, matches / len(required_lower))

    def _score_location_match(self, job_location: str, preferred_location: str, work_mode: str) -> float:
        """Score location match considering work mode preference."""
        if not job_location:
            return 0.5  # Default if no location info
        
        job_location = job_location.lower()
        
        # Remote work preference
        if work_mode == "Remote" and "remote" in job_location:
            return 1.0
        
        # On-site preference with location match
        if work_mode in ["On-site", "Hybrid"] and preferred_location:
            preferred_location = preferred_location.lower()
            if preferred_location in job_location:
                return 1.0
            
            # Check for city/state match
            location_parts = preferred_location.split(',')
            if any(part.strip() in job_location for part in location_parts):
                return 0.8
        
        # Any work mode
        if work_mode == "Any":
            if not preferred_location:
                return 0.7
            
            preferred_location = preferred_location.lower()
            if preferred_location in job_location:
                return 1.0
            
            # Check for city/state match
            location_parts = preferred_location.split(',')
            if any(part.strip() in job_location for part in location_parts):
                return 0.8
        
        return 0.4  # Low match

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process and score job listings."""
        resume_data = state.get("resume_data")
        job_listings = state.get("job_listings", [])
        preferences = state.get("feedback", {})
        
        if not resume_data or not job_listings:
            state["analysis_complete"] = True
            state["scored_listings"] = []
            return state
        
        # Convert resume_data to dict if it's not already
        resume_dict = resume_data
        if hasattr(resume_data, "dict"):
            resume_dict = resume_data.dict()
        
        # Score each job
        scored_listings = []
        for job in job_listings:
            score_result = self._score_job(job, resume_dict, preferences)
            
            # Combine job data with score data
            scored_job = {**job}
            scored_job["total_score"] = score_result["total_score"]
            scored_job["score_breakdown"] = score_result["score_breakdown"]
            scored_job["match_details"] = score_result["match_details"]
            
            scored_listings.append(scored_job)
        
        # Sort by total score
        scored_listings.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Update state
        state["analysis_complete"] = True
        state["scored_listings"] = scored_listings
        
        return state