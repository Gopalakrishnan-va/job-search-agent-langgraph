from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .base import BaseAgent
from ..config.settings import OPENAI_API_KEY, OPENAI_MODEL

class FeedbackRefinerAgent(BaseAgent):
    def __init__(self, apify_client):
        super().__init__(apify_client)
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3
        )

    def _get_system_prompt(self) -> str:
        return """
        You are a Feedback Refiner Agent responsible for:
        1. Processing user feedback
        2. Adjusting search parameters
        3. Improving match quality
        
        When given feedback about job search results, you should:
        - Identify what aspects of the search need improvement
        - Suggest modifications to search parameters
        - Provide guidance on how to get better matches
        
        Your output should be structured as actionable changes to the search process.
        """

    def _process_feedback(self, feedback: Dict[str, Any], current_results: list) -> Dict[str, Any]:
        """Process user feedback to refine search parameters."""
        # For now, we'll just pass through the feedback
        # In a real implementation, this would analyze feedback and suggest changes
        
        # Example of how this could be implemented with LLM
        if feedback and current_results:
            feedback_str = "\n".join([f"{k}: {v}" for k, v in feedback.items()])
            results_summary = "\n".join([
                f"Job {i+1}: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')} - Score: {job.get('total_score', 0)}"
                for i, job in enumerate(current_results[:3])  # Summarize top 3 results
            ])
            
            prompt = f"""
            Based on the user's preferences and the current search results, suggest refinements to improve matches.
            
            USER PREFERENCES:
            {feedback_str}
            
            CURRENT TOP RESULTS:
            {results_summary}
            
            What adjustments should be made to get better matches?
            """
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # In a real implementation, we would parse this response
            # and extract specific parameter adjustments
            
            return {
                "original_feedback": feedback,
                "refinement_suggestions": response.content,
                "adjusted_parameters": feedback  # For now, just pass through
            }
        
        return {"adjusted_parameters": feedback or {}}

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback and refine search."""
        feedback = state.get("feedback", {})
        scored_listings = state.get("scored_listings", [])
        
        # Process feedback to get refinements
        refinements = self._process_feedback(feedback, scored_listings)
        
        # Update state with refinements
        state["feedback_processed"] = True
        state["search_refinements"] = refinements
        
        return state