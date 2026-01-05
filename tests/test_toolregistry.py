import unittest

from pydantic import BaseModel, Field

from src.core.registry import ToolRegistry
from src.interfaces.tool import Tool


class DummyInput(BaseModel):
    query: str = Field(..., description="Search query")


class DummyTool(Tool):
    name = "dummy"
    description = "Dummy tool for tests"
    input_model = DummyInput

    def run(self, **kwargs):
        return kwargs


class TestToolRegistrySchema(unittest.TestCase):
    def test_get_schemas_returns_tool_schema(self):
        registry = ToolRegistry()
        registry.register(DummyTool())

        schemas = registry.get_schemas()

        self.assertEqual(len(schemas), 1)
        schema = schemas[0]
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], DummyTool.name)
        self.assertEqual(schema["function"]["description"], DummyTool.description)
        self.assertEqual(
            schema["function"]["parameters"],
            DummyInput.model_json_schema(),
        )


if __name__ == "__main__":
    unittest.main()
