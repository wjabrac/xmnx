from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.events.types import Event

class LLMProvider(ABC):
    """
    Abstract Interface for connecting to LLMs (OpenAI, Anthropic, Local).
    Decouples the logic from the specific model API.
    """
    
    @abstractmethod
    def completion(self, 
                   messages: List[Dict[str, str]], 
                   tools: Optional[List[Dict]] = None,
                   temperature: float = 0.0) -> str:
        """
        Get a simple completion.
        """
        pass

    @abstractmethod
    def structured_completion(self, 
                            messages: List[Dict[str, str]], 
                            response_model: Any) -> Any:
        """
        Get a structured response (Pydantic model) using Instructor/Tool Calling.
        """
        pass
