from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime

class WorkExperience(BaseModel):
    title: str
    company: str
    duration: str
    description: Optional[str] = None

class Education(BaseModel):
    degree: str
    institution: str
    year: str
    field: Optional[str] = None

class ResumeData(BaseModel):
    skills: List[str]
    experience: List[WorkExperience]
    education: List[Education]
    desired_role: str
    location_preference: str
    industry_experience: List[str]
    total_years_experience: float

class JobListing(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    remote_status: Optional[str] = None
    required_experience: Optional[str] = None
    responsibilities: List[str]
    required_skills: List[str]
    salary_info: Optional[Union[str, int, float]] = None
    posted_date: datetime
    application_url: str
    source: str = Field(..., description="Source platform (e.g., LinkedIn, Indeed)")

class ScoredJobListing(JobListing):
    total_score: float
    score_breakdown: Dict[str, float]
    match_details: Dict[str, str]

class JobSearchState(BaseModel):
    resume_text: str
    resume_parsed: bool = False
    jobs_scraped: bool = False
    analysis_complete: bool = False
    current_phase: str = "init"
    next_step: str = "resume_parser"
    resume_data: Optional[ResumeData] = None
    resume_summary: Optional[str] = None
    job_listings: List[Dict[str, Any]] = Field(default_factory=list)
    scored_listings: List[Dict[str, Any]] = Field(default_factory=list)
    feedback: Dict[str, Any] = Field(default_factory=dict)
    error_log: List[str] = Field(default_factory=list)