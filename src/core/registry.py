from typing import Dict, List, Any
from src.interfaces.tool import Tool

class ToolRegistry:
    """
    Central repository for all available tools.
    Allows retrieval by name and export of schemas for the LLM.
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered.")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns list of schemas for LLM tool binding."""
        return [tool.schema for tool in self._tools.values()]
