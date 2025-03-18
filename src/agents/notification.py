from typing import Dict, Any, List
from datetime import datetime
from .base import BaseAgent

class NotificationAgent(BaseAgent):
    def __init__(self, apify_client):
        super().__init__(apify_client)

    def _get_system_prompt(self) -> str:
        return """
        Notification Agent responsible for:
        1. Tracking job application status
        2. Sending notifications
        3. Managing communication
        """

    def _format_results_summary(self, scored_listings: List[Dict[str, Any]]) -> str:
        """Format a summary of the job search results."""
        if not scored_listings:
            return "No matching jobs found."
        
        summary_lines = ["## Job Search Results Summary", ""]
        
        # Add timestamp
        summary_lines.append(f"Search completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append(f"Total matches found: {len(scored_listings)}")
        summary_lines.append("")
        
        # Add top matches
        summary_lines.append("### Top Matches")
        for i, job in enumerate(scored_listings[:5], 1):  # Top 5 matches
            title = job.get("title", "Unknown Position")
            company = job.get("company", "Unknown Company")
            location = job.get("location", "Unknown Location")
            score = job.get("total_score", 0)
            url = job.get("url", job.get("application_url", "#"))
            
            summary_lines.append(f"{i}. **{title}** at {company}")
            summary_lines.append(f"   - Location: {location}")
            summary_lines.append(f"   - Match Score: {score:.1f}%")
            summary_lines.append(f"   - [Apply Now]({url})")
            summary_lines.append("")
        
        # Add skill insights if available
        skills_mentioned = self._extract_common_skills(scored_listings)
        if skills_mentioned:
            summary_lines.append("### Most Requested Skills")
            for skill, count in skills_mentioned[:5]:
                summary_lines.append(f"- {skill}: mentioned in {count} jobs")
            summary_lines.append("")
        
        return "\n".join(summary_lines)

    def _extract_common_skills(self, jobs: List[Dict[str, Any]]) -> List[tuple]:
        """Extract commonly mentioned skills from job listings."""
        skill_count = {}
        for job in jobs:
            skills = job.get("required_skills", [])
            for skill in skills:
                skill_count[skill] = skill_count.get(skill, 0) + 1
        
        # Sort by frequency
        return sorted(skill_count.items(), key=lambda x: x[1], reverse=True)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process notifications and updates."""
        scored_listings = state.get("scored_listings", [])
        
        # Generate results summary
        results_summary = self._format_results_summary(scored_listings)
        
        # Update state
        state["notification_sent"] = True
        state["results_summary"] = results_summary
        state["next_step"] = "complete"  # Mark workflow as complete
        
        return state