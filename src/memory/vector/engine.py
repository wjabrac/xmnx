import lancedb
from typing import List, Dict, Any
from src.core.events.types import Event

class VectorEngine:
    """
    Local Vector Store using LanceDB.
    Indexed by embedding functionality (to be plugged in).
    """
    def __init__(self, db_path: str = "lancedb"):
        self.db = lancedb.connect(db_path)
        self.table_name = "memory_embeddings"
        self._init_table()

    def _init_table(self):
        # Using a simple schema for now, relying on PyArrow inference when adding
        # Schema: vector, text, task_id, event_id
        pass

    def add_event(self, event: Event, embedding: List[float]):
        """
        Add an event to the vector store.
        """
        table = self.db.create_table(
            self.table_name,
            data=[{
                "vector": embedding,
                "text": str(event.content),
                "task_id": event.task_id or "global",
                "event_id": event.id,
                "type": event.type
            }],
            mode="append"
        )

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        if self.table_name not in self.db.table_names():
            return []
            
        table = self.db.open_table(self.table_name)
        results = table.search(query_vector).limit(limit).to_pandas()
        return results.to_dict(orient="records")
