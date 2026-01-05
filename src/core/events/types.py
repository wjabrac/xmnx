from datetime import datetime
from typing import Dict, Any, Optional, Literal
from uuid import uuid4, UUID
from pydantic import BaseModel, Field

EventType = Literal["thought", "action", "observation", "control"]

class Event(BaseModel):
    """
    The atomic unit of the Agent's consciousness.
    Everything that happens is an Event in the stream.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str  # e.g., "planner", "sandbox", "user"
    type: EventType
    content: Dict[str, Any]
    
    # Traceability
    task_id: Optional[str] = None
    parent_id: Optional[str] = None  # Causal link (e.g., Observation -> Action)

class ActionEvent(Event):
    type: Literal["action"] = "action"
    tool: str
    args: Dict[str, Any]

class ObservationEvent(Event):
    type: Literal["observation"] = "observation"
    output: str
    error: Optional[str] = None
    exit_code: int = 0
