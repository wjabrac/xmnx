from typing import Any, Optional
from pydantic import BaseModel, Field

from src.interfaces.tool import Tool
from src.runtime.sandbox.interface import Sandbox


class EditFileInput(BaseModel):
    path: str = Field(..., description="Absolute path to the file to edit")
    search: str = Field(..., description="Exact text to search for")
    replace: str = Field(..., description="Replacement text")
    count: Optional[int] = Field(
        None,
        description="Maximum number of replacements to perform. Defaults to all matches.",
    )


class EditFileTool(Tool):
    name = "edit_file"
    description = "Edit a file by performing a literal search-and-replace."
    input_model = EditFileInput

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def run(self, path: str, search: str, replace: str, count: Optional[int] = None) -> Any:
        if search == "":
            return {"error": "Search string cannot be empty."}

        try:
            content = self.sandbox.read_file(path)
            total_matches = content.count(search)
            if total_matches == 0:
                return {"error": "Search string not found.", "path": path}

            if count is None:
                updated_content = content.replace(search, replace)
                replacements = total_matches
            else:
                if count <= 0:
                    return {"error": "Count must be a positive integer.", "path": path}
                updated_content = content.replace(search, replace, count)
                replacements = min(count, total_matches)

            self.sandbox.write_file(path, updated_content)
            return {
                "status": "success",
                "path": path,
                "replacements": replacements,
            }
        except Exception as e:
            return {"error": str(e), "path": path}


class LintFileInput(BaseModel):
    path: str = Field(..., description="Absolute path to the file to lint")
    command: str = Field(
        "python -m py_compile",
        description=(
            "Lint command to run. If it includes '{path}', it will be replaced with the file path."
        ),
    )
    timeout: int = Field(60, description="Max execution time in seconds")


class LintTool(Tool):
    name = "lint_file"
    description = "Run a linter against a single file."
    input_model = LintFileInput

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def run(self, path: str, command: str = "python -m py_compile", timeout: int = 60) -> Any:
        try:
            if "{path}" in command:
                lint_command = command.replace("{path}", path)
            else:
                lint_command = f"{command} {path}"

            exit_code, stdout, stderr = self.sandbox.execute(lint_command, timeout)
            return {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "command": lint_command,
            }
        except Exception as e:
            return {"error": str(e), "path": path}
