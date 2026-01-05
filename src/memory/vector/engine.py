import json
import lancedb
from typing import List, Dict, Any, Optional
from src.core.events.types import Event
from litellm import embedding

class VectorEngine:
    """
    Local Vector Store using LanceDB.
    Indexed by embedding functionality (to be plugged in).
    """
    def __init__(self, db_path: str = "lancedb"):
        self.db = lancedb.connect(db_path)
        self.table_name = "memory_embeddings"
        self.document_table_name = "memory_documents"
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

    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        words = text.split()
        if not words:
            return []

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))

            if end == len(words):
                break

            start = max(end - chunk_overlap, 0)

        return chunks

    def _embed_texts(self, texts: List[str], embedding_model: str) -> List[List[float]]:
        if not texts:
            return []
        response = embedding(
            model=embedding_model,
            input=texts
        )
        return [item["embedding"] for item in response["data"]]

    def index_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 400,
        chunk_overlap: int = 80,
        embedding_model: str = "text-embedding-3-small"
    ) -> int:
        """
        Chunk and index a document into the vector store.
        """
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        if not chunks:
            return 0

        embeddings = self._embed_texts(chunks, embedding_model)
        records = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            records.append({
                "vector": vector,
                "text": chunk,
                "document_id": document_id,
                "chunk_id": idx,
                "metadata": json.dumps(metadata or {})
            })

        self.db.create_table(
            self.document_table_name,
            data=records,
            mode="append"
        )
        return len(records)

    def search_memory(
        self,
        query: str,
        limit: int = 5,
        embedding_model: str = "text-embedding-3-small"
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over indexed document chunks.
        """
        if self.document_table_name not in self.db.table_names():
            return []

        query_vector = self._embed_texts([query], embedding_model)[0]
        table = self.db.open_table(self.document_table_name)
        results = table.search(query_vector).limit(limit).to_pandas()
        records = results.to_dict(orient="records")
        for record in records:
            record.pop("vector", None)
        return records

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        if self.table_name not in self.db.table_names():
            return []
            
        table = self.db.open_table(self.table_name)
        results = table.search(query_vector).limit(limit).to_pandas()
        return results.to_dict(orient="records")
