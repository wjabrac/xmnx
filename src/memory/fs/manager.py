import os
from pathlib import Path
from typing import Dict, Optional
from src.core.events.stream import EventStream

class BrainManager:
    """
    Manages the filesystem memory ("UUID Brain").
    Each Task ID gets a dedicated folder with its own EventStream.
    """
    def __init__(self, base_path: str = "brain"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.streams: Dict[str, EventStream] = {}

    def get_stream(self, task_id: str) -> EventStream:
        if task_id in self.streams:
            return self.streams[task_id]
        
        # Determine path: brain/{task_id}/events.jsonl
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        persistence_path = task_dir / "events.jsonl"
        stream = EventStream(persistence_path=str(persistence_path))
        
        self.streams[task_id] = stream
        return stream

    def list_tasks(self):
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]
