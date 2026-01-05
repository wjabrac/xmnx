from typing import Any, Type
from pydantic import BaseModel, Field
from src.interfaces.tool import Tool
from src.runtime.sandbox.interface import Sandbox

class ShellInput(BaseModel):
    command: str = Field(..., description="The shell command to execute")
    timeout: int = Field(60, description="Max execution time in seconds")

class ShellTool(Tool):
    name = "execute_command"
    description = "Execute a shell command in the sandbox. Returns stdout, stderr, and exit code."
    input_model = ShellInput

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def run(self, command: str, timeout: int = 60) -> Any:
        exit_code, stdout, stderr = self.sandbox.execute(command, timeout)
        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr
        }
