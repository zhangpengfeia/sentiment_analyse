from collections import deque

from engines.common.eventing.bus import subscribe, unsubscribe
from engines.common.eventing.event import EventType
from engines.contracts.dimensions import DIMENSIONS


class HostService:

    def __init__(self):
        self._discussion_records = deque(maxlen=1000)

    def subscribe_discussion(self):
        subscribe(EventType.HOST_DISCUSSION_MESSAGE, self._record_discussion)

    def unsubscribe_discussion(self):
        unsubscribe(self._record_discussion)

    def _record_discussion(self, event_type, data):
        self._discussion_records.append({
            "speaker_name": data.get("sender", ""),
            "message_text": data.get("content", ""),
            "sent_at": data.get("timestamp", ""),
            "dimension_key": data.get("section_key", ""),
        })

    def start_host(self):
        pass

    def stop_host(self):
        pass

    def get_discussion_records(self):
        return {"discussion_records": list(self._discussion_records)}

    def get_research_dimensions(self):
        return [
            {"key": dimension.key, "title": dimension.title, "index": str(index)}
            for index, dimension in enumerate(DIMENSIONS.values(), start=1)
        ]
