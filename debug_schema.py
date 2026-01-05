import json
from src.runtime.sandbox.local import LocalSandbox
from src.core.tools.filesystem import WriteFileTool

sandbox = LocalSandbox("workspace")
tool = WriteFileTool(sandbox)
schema = tool.schema

print(json.dumps(schema, indent=2))
