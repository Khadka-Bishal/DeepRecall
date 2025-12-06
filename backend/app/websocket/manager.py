"""WebSocket connection management."""

from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        """Accept and store a new WebSocket connection."""
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        """Remove a WebSocket connection."""
        try:
            self.active_connections.remove(ws)
        except ValueError:
            pass

    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        for conn in list(self.active_connections):
            try:
                await conn.send_json(message)
            except Exception:
                self.disconnect(conn)

    async def send_personal_message(self, message: str, ws: WebSocket):
        """Send a message to a specific client."""
        try:
            await ws.send_text(message)
        except Exception:
            self.disconnect(ws)


# Global connection manager instance
_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
