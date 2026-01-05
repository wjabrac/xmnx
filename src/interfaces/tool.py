from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel

class Tool(ABC):
    """
    Abstract Base Class for XMNX Tools.
    Follows Model Context Protocol (MCP) principles:
    - name: Unique identifier
    - description: Semantically rich help text for the LLM
    - input_schema: Pydantic model defining arguments
    """
    name: str
    description: str
    input_model: Type[BaseModel]

    @abstractmethod
    def run(self, **kwargs) -> Any:
        pass

    @property
    def schema(self) -> Dict[str, Any]:
        """Returns the JSON Schema for the tool (OpenAI compatible)."""
        model_schema = self.input_model.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": model_schema
            }
        }
