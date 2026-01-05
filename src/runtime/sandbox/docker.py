import json
import os
from pathlib import Path
import subprocess
from typing import Tuple, List, Optional

from src.runtime.sandbox.interface import Sandbox


class DockerSandbox(Sandbox):
    """
    Executes commands inside a Docker container for isolation.
    """
    def __init__(
        self,
        work_dir: str = ".",
        image: str = "xmnx-sandbox:latest",
        dockerfile: str = "Dockerfile",
        build_context: Optional[str] = None,
        auto_build: bool = True,
    ):
        self.work_dir = os.path.abspath(work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        self.image = image
        self.dockerfile = os.path.abspath(dockerfile)
        self.build_context = build_context or os.path.dirname(self.dockerfile) or "."

        if auto_build:
            self._ensure_image()

    def _ensure_image(self) -> None:
        inspect = subprocess.run(
            ["docker", "image", "inspect", self.image],
            capture_output=True,
            text=True,
        )
        if inspect.returncode == 0:
            return

        build = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                self.image,
                "-f",
                self.dockerfile,
                self.build_context,
            ],
            capture_output=True,
            text=True,
        )
        if build.returncode != 0:
            raise RuntimeError(
                f"Failed to build Docker image {self.image}: {build.stderr}"
            )

    def execute(self, cmd: str, timeout: int = 60) -> Tuple[int, str, str]:
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{self.work_dir}:/workspace",
            "-w",
            "/workspace",
            self.image,
            "/bin/sh",
            "-c",
            cmd,
        ]
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    def read_file(self, path: str) -> str:
        full_path = self._resolve_path(path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: str, content: str):
        full_path = self._resolve_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def list_files(self, path: str = ".") -> List[str]:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
            return []
        return os.listdir(full_path)

    def _resolve_path(self, path: str) -> str:
        base_path = Path(self.work_dir).resolve(strict=False)
        target_path = (base_path / path).resolve(strict=False)
        if base_path == target_path or base_path in target_path.parents:
            return str(target_path)
        raise PermissionError(f"Access denied: {path}")

    def snapshot(self) -> str:
        snap_path = os.path.join(self.work_dir, "snapshot_latest.json")
        state = {
            "cwd": self.work_dir,
            "env": dict(os.environ),
            "docker_image": self.image,
        }
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        return snap_path
