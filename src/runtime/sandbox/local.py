import hashlib
import os
import subprocess
import sys
from datetime import datetime
from typing import Tuple, List

from src.runtime.sandbox.interface import Sandbox

class LocalSandbox(Sandbox):
    """
    Executes commands on the local host (CAUTION: No isolation).
    Used for the initial 'Bootstrap' phase or when running in a dedicated VM.
    """
    def __init__(self, work_dir: str = "."):
        self.work_dir = os.path.abspath(work_dir)
        os.makedirs(self.work_dir, exist_ok=True)

    def execute(self, cmd: str, timeout: int = 60) -> Tuple[int, str, str]:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    def read_file(self, path: str) -> str:
        full_path = os.path.join(self.work_dir, path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: str, content: str):
        full_path = os.path.join(self.work_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def list_files(self, path: str = ".") -> List[str]:
        full_path = os.path.join(self.work_dir, path)
        if not os.path.exists(full_path):
            return []
        return os.listdir(full_path)

    def snapshot(self) -> str:
        """
        Capture current environment state to a JSON file.
        """
        import json
        snap_path = os.path.join(self.work_dir, "snapshot_latest.json")
        safe_env_keys = {
            "PATH",
            "PWD",
            "LANG",
            "LC_ALL",
            "TZ",
            "TERM",
        }
        safe_env = {k: os.environ[k] for k in safe_env_keys if k in os.environ}
        sensitive_keys = {
            "OPENAI_API_KEY",
            "GITHUB_TOKEN",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "GOOGLE_APPLICATION_CREDENTIALS",
        }
        env_hashes = {
            key: hashlib.sha256(os.environ[key].encode("utf-8")).hexdigest()
            for key in sensitive_keys
            if key in os.environ
        }
        state = {
            "cwd": self.work_dir,
            "env": safe_env,
            "env_hashes": env_hashes,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "snapshot_version": "v2",
            "argv": list(sys.argv),
        }
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        return snap_path
