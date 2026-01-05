from src.runtime.sandbox.local import LocalSandbox
from src.core.tools.filesystem import WriteFileTool
import os

# Setup
workspace = "z:/home/willux/Others/XMNX/workspace"
sandbox = LocalSandbox(work_dir=workspace)
tool = WriteFileTool(sandbox)

# Execute
print("Testing WriteFileTool...")
result = tool.run(path="z:/home/willux/Others/XMNX/workspace/unit_test.txt", content="Success")
print(f"Tool Result: {result}")

# Verify
exists = os.path.exists("z:/home/willux/Others/XMNX/workspace/unit_test.txt")
print(f"File Exists: {exists}")
