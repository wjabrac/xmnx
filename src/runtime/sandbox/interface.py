from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class Sandbox(ABC):
    """
    Abstract Interface for the Agent's Execution Environment.
    Follows the "Sidecar" pattern: Agent requests action -> Sandbox executes.
    """
    
    @abstractmethod
    def execute(self, cmd: str, timeout: int = 60) -> Tuple[int, str, str]:
        """
        Execute a shell command.
        Returns: (exit_code, stdout, stderr)
        """
        pass

    @abstractmethod
    def read_file(self, path: str) -> str:
        pass

    @abstractmethod
    def write_file(self, path: str, content: str):
        pass

    @abstractmethod
    def list_files(self, path: str) -> list[str]:
        pass

    @abstractmethod
    def snapshot(self) -> str:
        """
        Capture the current state (Env, Aliases, CWD) for resumption.
        Returns a path to the snapshot file or a state ID.
        """
        pass
