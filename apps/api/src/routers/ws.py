import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..events.bus import event_bus
from ..schemas.event import SystemEvent

logger = logging.getLogger("router.ws")
router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Connected clients
dashboard_clients: Set[WebSocket] = set()
call_clients: Dict[str, Set[WebSocket]] = {}


async def broadcast_to_dashboard(event: SystemEvent) -> None:
    if not dashboard_clients:
        return

    payload = json.dumps({
        "id": event.id,
        "event": event.event,
        "call_id": event.call_id,
        "agent_id": event.agent_id,
        "data": event.data,
        "timestamp": event.timestamp.isoformat(),
    })

    for ws in list(dashboard_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dashboard_clients.discard(ws)


async def broadcast_to_call_subscribers(event: SystemEvent) -> None:
    if not event.call_id or event.call_id not in call_clients:
        return

    payload = json.dumps({
        "id": event.id,
        "event": event.event,
        "call_id": event.call_id,
        "data": event.data,
        "timestamp": event.timestamp.isoformat(),
    })

    for ws in list(call_clients[event.call_id]):
        try:
            await ws.send_text(payload)
        except Exception:
            call_clients[event.call_id].discard(ws)


# Subscribe event bus to web socket broadcast
event_bus.subscribe(broadcast_to_dashboard)
event_bus.subscribe(broadcast_to_call_subscribers)


@router.websocket("/dashboard")
async def ws_dashboard(websocket: WebSocket):
    await websocket.accept()
    dashboard_clients.add(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({"event": "connected", "message": "Subscribed to dashboard stream"})
        while True:
            # Keep connection alive, listen for ping/heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        dashboard_clients.discard(websocket)
    except Exception as e:
        logger.debug(f"Dashboard WS error: {e}")
        dashboard_clients.discard(websocket)


@router.websocket("/calls/{call_id}")
async def ws_call_detail(websocket: WebSocket, call_id: str):
    await websocket.accept()
    if call_id not in call_clients:
        call_clients[call_id] = set()
    call_clients[call_id].add(websocket)

    try:
        await websocket.send_json({"event": "connected", "call_id": call_id})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if call_id in call_clients:
            call_clients[call_id].discard(websocket)
            if not call_clients[call_id]:
                del call_clients[call_id]
    except Exception as e:
        logger.debug(f"Call WS error: {e}")
        if call_id in call_clients:
            call_clients[call_id].discard(websocket)
