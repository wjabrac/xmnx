import json
from typing import List, Callable, Optional
from pathlib import Path
from src.core.events.types import Event

Subscriber = Callable[[Event], None]

class EventStream:
    """
    The Central Nervous System of the Agent.
    Implements the "Log-Structured" pattern from OpenDevin + Antigravity.
    """
    def __init__(self, persistence_path: Optional[str] = None):
        self.events: List[Event] = []
        self.subscribers: List[Subscriber] = []
        self.persistence_path = Path(persistence_path) if persistence_path else None
        
        if self.persistence_path:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            # Rehydrate if exists
            if self.persistence_path.exists():
                self._rehydrate()

    def subscribe(self, callback: Subscriber):
        self.subscribers.append(callback)

    def publish(self, event: Event):
        self.events.append(event)
        
        # 1. Notify Subscribers (Synchronous for now)
        for sub in self.subscribers:
            try:
                sub(event)
            except Exception as e:
                print(f"Error in subscriber: {e}")
        
        # 2. Persist to Disk (Append-Only)
        if self.persistence_path:
            with open(self.persistence_path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

    def _rehydrate(self):
        """Reload consciousness from disk."""
        with open(self.persistence_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        event = Event(**data)
                        self.events.append(event)
                    except Exception as e:
                        print(f"Failed to rehydrate event: {e}")

    def get_history(self) -> List[Event]:
        return self.events
