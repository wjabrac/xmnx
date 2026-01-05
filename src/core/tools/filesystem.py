from typing import Any, Type
from pydantic import BaseModel, Field
from src.interfaces.tool import Tool
from src.runtime.sandbox.interface import Sandbox

# --- Read File ---
class ReadFileInput(BaseModel):
    path: str = Field(..., description="Absolute path to the file to read")

class ReadFileTool(Tool):
    name = "read_file"
    description = "Read the contents of a file."
    input_model = ReadFileInput

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def run(self, path: str) -> Any:
        try:
            content = self.sandbox.read_file(path)
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}

# --- Write File ---
class WriteFileInput(BaseModel):
    path: str = Field(..., description="Absolute path to write to")
    content: str = Field(..., description="Content to write")

class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file. Overwrites if exists."
    input_model = WriteFileInput

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def run(self, path: str, content: str) -> Any:
        try:
            self.sandbox.write_file(path, content)
            return {"status": "success", "path": path}
        except Exception as e:
            return {"error": str(e)}

# --- List Files ---
class ListFilesInput(BaseModel):
    path: str = Field(..., description="Directory path to list")

class ListFilesTool(Tool):
    name = "list_files"
    description = "List files and directories in a given path."
    input_model = ListFilesInput

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def run(self, path: str) -> Any:
        try:
            files = self.sandbox.list_files(path)
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}
