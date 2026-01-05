import os
import json
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from litellm import completion
from src.interfaces.llm import LLMProvider

T = TypeVar("T", bound=BaseModel)

class LiteLLMProvider(LLMProvider):
    """
    Concrete implementation using LiteLLM (The "Grand Unifier").
    Supports OpenAI, Anthropic, Ollama, etc.
    """
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def completion(self, 
                   messages: List[Dict[str, str]], 
                   tools: Optional[List[Dict]] = None,
                   temperature: float = 0.0) -> str:
        
        response = completion(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            api_key=self.api_key
        )
        return response.choices[0].message.content

    def structured_completion(self, 
                            messages: List[Dict[str, str]], 
                            response_model: Type[T]) -> T:
        """
        Uses LiteLLM's `response_format` or tool-calling mode to get structured data.
        For simplicity in this scaffold, we'll force JSON mode or Tool Call.
        """
        # Strategy: Use Instructor-like patching or just raw function calling
        # Here we use the "Function Call" trick:
        schema = response_model.model_json_schema()
        tool_name = schema.get("title", "Response")
        
        tool_definition = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Output the structured {tool_name}",
                "parameters": schema
            }
        }
        
        response = completion(
            model=self.model,
            messages=messages,
            tools=[tool_definition],
            tool_choice={"type": "function", "function": {"name": tool_name}},
            temperature=0.0,
            api_key=self.api_key
        )
        
        tool_call = response.choices[0].message.tool_calls[0]
        arguments_json = tool_call.function.arguments
        return response_model.model_validate_json(arguments_json)
