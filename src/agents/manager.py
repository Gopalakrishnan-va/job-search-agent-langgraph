from typing import Dict, Any
from .base import BaseAgent

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(None)  # Manager doesn't need Apify client
    
    def _get_system_prompt(self) -> str:
        return """
        Manager Agent responsible for:
        1. Coordinating the job search workflow
        2. Determining next steps based on current state
        3. Handling transitions between agents
        """
    
    async def determine_next_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the next step in the workflow."""
        # Check for errors
        if state.get("error_log") and len(state["error_log"]) > 0:
            state["next_step"] = "complete"
            return state
            
        # Normal workflow progression
        if not state.get("resume_parsed", False):
            state["next_step"] = "resume_parser"
        elif not state.get("jobs_scraped", False):
            state["next_step"] = "job_scraper"
        elif not state.get("analysis_complete", False):
            state["next_step"] = "relevance_scorer"
        elif not state.get("feedback_processed", False):
            state["next_step"] = "feedback_refiner"
        elif not state.get("notification_sent", False):
            state["next_step"] = "notification"
        else:
            state["next_step"] = "complete"
            
        return state
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state."""
        # Log the current phase
        current_phase = state.get("current_phase", "init")
        next_phase = state.get("next_step", "unknown")
        
        # Update the current phase
        state["current_phase"] = next_phase
        
        # Determine the next step
        return await self.determine_next_step(state)