import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.core.redis import (
    publish_tracking_event,
)
from app.models.user import UserRole
from app.models.driver import Driver
from app.models.location import DriverLocation
from app.schemas.tracking import LocationUpdateMessage

logger = logging.getLogger(__name__)

ws_router = APIRouter()


class TrackingConnectionManager:
    """
    Manages active WebSocket connections segregated by user role:
    - Manager/Admin subscribers: Receive real-time fleet GPS broadcasts.
    - Driver publishers: Transmit their own vehicle telemetry.
    """

    def __init__(self):
        self.active_connections: Dict[WebSocket, dict] = {}
        self.manager_connections: Set[WebSocket] = set()
        self.driver_connections: Dict[str, Set[WebSocket]] = {}
        self._redis_listener_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_info: dict):
        await websocket.accept()
        self.active_connections[websocket] = user_info
        role = user_info.get("role")
        driver_id = user_info.get("driver_id")

        if role in [UserRole.ADMIN.value, UserRole.LOGISTICS_MANAGER.value]:
            self.manager_connections.add(websocket)
            logger.info(f"Manager WebSocket connected (User: {user_info.get('name')}). Total managers: {len(self.manager_connections)}")
        elif role == UserRole.DRIVER.value and driver_id:
            if driver_id not in self.driver_connections:
                self.driver_connections[driver_id] = set()
            self.driver_connections[driver_id].add(websocket)
            logger.info(f"Driver WebSocket connected (Driver: {driver_id}).")

        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to Smart Logistics Live Telemetry Stream",
            "authenticated_as": {
                "user_id": user_info.get("user_id"),
                "name": user_info.get("name"),
                "role": role,
                "driver_id": driver_id,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

    def disconnect(self, websocket: WebSocket):
        user_info = self.active_connections.pop(websocket, None)
        if user_info:
            if websocket in self.manager_connections:
                self.manager_connections.remove(websocket)
            driver_id = user_info.get("driver_id")
            if driver_id and driver_id in self.driver_connections:
                self.driver_connections[driver_id].discard(websocket)
                if not self.driver_connections[driver_id]:
                    del self.driver_connections[driver_id]
            logger.info(f"WebSocket client disconnected: {user_info.get('name')}")

    async def broadcast_to_managers(self, message: dict):
        """Broadcasts telemetry update to all connected manager/admin dashboards."""
        dead_connections = []
        for ws in list(self.manager_connections):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending to manager client: {e}")
                dead_connections.append(ws)

        for dead in dead_connections:
            self.disconnect(dead)

    async def send_to_driver(self, driver_id: str, message: dict):
        """Sends message directly to a specific driver's active sockets."""
        sockets = self.driver_connections.get(driver_id, set())
        dead_connections = []
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)

        for dead in dead_connections:
            self.disconnect(dead)


tracking_manager = TrackingConnectionManager()


async def resolve_driver_for_user(user_id: str) -> Optional[dict]:
    """Resolves driver profile corresponding to user_id directly from the database."""
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Driver).where(Driver.user_id == user_id))
            drv = res.scalar_one_or_none()
            if drv:
                return {
                    "id": drv.id,
                    "name": "Driver",
                    "status": drv.status,
                    "current_latitude": drv.current_latitude,
                    "current_longitude": drv.current_longitude,
                }
            # Fallback by direct driver id
            res2 = await session.execute(select(Driver).where(Driver.id == user_id))
            drv2 = res2.scalar_one_or_none()
            if drv2:
                return {
                    "id": drv2.id,
                    "name": "Driver",
                    "status": drv2.status,
                    "current_latitude": drv2.current_latitude,
                    "current_longitude": drv2.current_longitude,
                }
    except Exception as e:
        logger.debug(f"DB driver lookup failed: {e}")
    return None


async def authenticate_ws_token(token: Optional[str]) -> Optional[dict]:
    """Authenticates JWT token for WebSocket connection."""
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
        name = payload.get("name")
        token_type = payload.get("type")

        if not user_id or token_type != "access":
            return None

        driver_id = None
        if role == UserRole.DRIVER.value:
            driver_info = await resolve_driver_for_user(user_id)
            if driver_info:
                driver_id = driver_info["id"]
                name = driver_info.get("name", name)
            else:
                driver_id = "drv-001"

        return {
            "user_id": user_id,
            "role": role,
            "name": name or "User",
            "driver_id": driver_id,
        }
    except Exception as e:
        logger.warning(f"WebSocket auth token validation error: {e}")
        return None


async def persist_driver_location(
    driver_id: str,
    latitude: float,
    longitude: float,
    accuracy: Optional[float],
    speed: Optional[float],
    heading: Optional[float],
    timestamp: datetime,
):
    """Persists driver location update to DB and updates Driver position."""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                loc_record = DriverLocation(
                    driver_id=driver_id,
                    latitude=latitude,
                    longitude=longitude,
                    accuracy=accuracy,
                    speed=speed,
                    heading=heading,
                    timestamp=timestamp,
                )
                session.add(loc_record)
                await session.execute(
                    update(Driver)
                    .where(Driver.id == driver_id)
                    .values(
                        current_latitude=latitude,
                        current_longitude=longitude,
                        updated_at=timestamp,
                    )
                )
    except Exception as e:
        logger.warning(f"Failed to persist driver location to DB: {e}")


@ws_router.websocket("/ws/tracking")
async def websocket_tracking_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Real-time WebSocket endpoint for fleet telemetry & live GPS tracking.
    Authenticate via query parameter '?token=<JWT_ACCESS_TOKEN>' or initial auth message.
    """
    user_info = await authenticate_ws_token(token)

    if not user_info:
        await websocket.accept()
        try:
            first_msg_raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            first_msg = json.loads(first_msg_raw)
            if first_msg.get("type") == "AUTH" and first_msg.get("token"):
                user_info = await authenticate_ws_token(first_msg["token"])
        except Exception:
            user_info = None

        if not user_info:
            await websocket.send_json({
                "type": "AUTH_ERROR",
                "message": "Unauthorized: Valid access token required for WebSocket tracking.",
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        tracking_manager.active_connections[websocket] = user_info
        role = user_info.get("role")
        driver_id = user_info.get("driver_id")
        if role in [UserRole.ADMIN.value, UserRole.LOGISTICS_MANAGER.value]:
            tracking_manager.manager_connections.add(websocket)
        elif role == UserRole.DRIVER.value and driver_id:
            if driver_id not in tracking_manager.driver_connections:
                tracking_manager.driver_connections[driver_id] = set()
            tracking_manager.driver_connections[driver_id].add(websocket)
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to Smart Logistics Live Telemetry Stream",
            "authenticated_as": user_info,
            "timestamp": datetime.utcnow().isoformat(),
        })
    else:
        await tracking_manager.connect(websocket, user_info)

    user_role = user_info.get("role")
    driver_id = user_info.get("driver_id")
    driver_name = user_info.get("name")

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                data = json.loads(data_text)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "ERROR", "message": "Invalid JSON format"})
                continue

            msg_type = data.get("type")

            if msg_type == "PING":
                await websocket.send_json({
                    "type": "PONG",
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif msg_type == "location_update":
                if user_role != UserRole.DRIVER.value:
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": "Forbidden: Only authenticated drivers can publish location updates.",
                    })
                    continue

                target_driver_id = driver_id
                if not target_driver_id:
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": "No active driver profile associated with this account.",
                    })
                    continue

                try:
                    loc_msg = LocationUpdateMessage(**data)
                except Exception as val_err:
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": f"Coordinate validation error: {val_err}",
                    })
                    continue

                event_timestamp = datetime.utcnow()

                await persist_driver_location(
                    driver_id=target_driver_id,
                    latitude=loc_msg.latitude,
                    longitude=loc_msg.longitude,
                    accuracy=loc_msg.accuracy,
                    speed=loc_msg.speed,
                    heading=loc_msg.heading,
                    timestamp=event_timestamp,
                )

                event_payload = {
                    "type": "driver_location_updated",
                    "driver_id": target_driver_id,
                    "driver_name": driver_name,
                    "latitude": loc_msg.latitude,
                    "longitude": loc_msg.longitude,
                    "accuracy": loc_msg.accuracy,
                    "speed": loc_msg.speed,
                    "heading": loc_msg.heading,
                    "timestamp": event_timestamp.isoformat(),
                }

                await publish_tracking_event(event_payload)
                await tracking_manager.broadcast_to_managers(event_payload)

                await websocket.send_json({
                    "type": "LOCATION_ACKNOWLEDGED",
                    "driver_id": target_driver_id,
                    "timestamp": event_timestamp.isoformat(),
                })

            else:
                await websocket.send_json({
                    "type": "MESSAGE_RECEIVED",
                    "message": f"Received {msg_type}",
                })

    except WebSocketDisconnect:
        tracking_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket tracking connection error: {e}")
        tracking_manager.disconnect(websocket)
