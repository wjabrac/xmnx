import tempfile
import unittest
from pathlib import Path

from src.core.events.stream import EventStream
from src.core.events.types import Event


class TestEventStreamPersistence(unittest.TestCase):
    def test_persist_and_rehydrate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence_path = Path(tmpdir) / "events.log"
            stream = EventStream(persistence_path=str(persistence_path))
            event = Event(
                source="test",
                type="observation",
                content={"message": "hello"},
            )

            stream.publish(event)

            rehydrated_stream = EventStream(persistence_path=str(persistence_path))

            self.assertEqual(len(rehydrated_stream.get_history()), 1)
            rehydrated_event = rehydrated_stream.get_history()[0]
            self.assertEqual(rehydrated_event.source, event.source)
            self.assertEqual(rehydrated_event.type, event.type)
            self.assertEqual(rehydrated_event.content, event.content)
            self.assertEqual(rehydrated_event.id, event.id)


if __name__ == "__main__":
    unittest.main()
