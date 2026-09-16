"""将进程内事件总线转发为浏览器可消费的 SSE 消息。"""

import asyncio
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from engines.common.eventing.bus import subscribe, unsubscribe
from engines.common.eventing.event import EventType


router = APIRouter(prefix="/api/events", tags=["实时事件"])


async def event_stream():
    queue = asyncio.Queue(maxsize=256)
    loop = asyncio.get_running_loop()

    def enqueue(message):
        if queue.full():
            queue.get_nowait()
        queue.put_nowait(message)

    def on_event(event_type, data):
        message = json.dumps({"event": event_type.value, "data": data}, ensure_ascii=False)
        loop.call_soon_threadsafe(enqueue, message)

    try:
        for event_type in EventType:
            subscribe(event_type, on_event)
        yield {"event": "connected", "data": "{}"}
        while True:
            yield {"data": await queue.get()}
    finally:
        unsubscribe(on_event)


@router.get("/stream")
async def stream_events():
    return EventSourceResponse(event_stream(), ping=15)
