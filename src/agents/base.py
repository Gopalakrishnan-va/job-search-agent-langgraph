from typing import Any, Dict, Optional
from apify_client import ApifyClient
from abc import ABC, abstractmethod
from ..utils.retry import with_retry

class BaseAgent(ABC):
    def __init__(self, apify_client: ApifyClient, actor_id: Optional[str] = None):
        self.apify_client = apify_client
        self.actor_id = actor_id
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return updated state."""
        pass

    @with_retry()
    def run_actor(self, actor_id: Optional[str] = None, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the associated Apify actor if one exists."""
        actor_id = actor_id or self.actor_id
        if not actor_id:
            raise ValueError("No actor_id specified for this agent")
        
        try:
            run = self.apify_client.actor(actor_id).call(run_input=input_data)
            dataset_items = self.apify_client.dataset(run["defaultDatasetId"]).list_items().items
            return dataset_items
        except Exception as e:
            # Log the error and re-raise
            error_msg = f"Error running actor {actor_id}: {str(e)}"
            print(error_msg)  # Replace with proper logging
            raise