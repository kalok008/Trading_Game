"""
WebSocket consumer for a live game session.
Implemented in Phase 3 — placeholder so ASGI routing loads cleanly for now.
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GameSessionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # TODO(Phase 3): auth check, group join, send initial snapshot
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive_json(self, content, **kwargs):
        # TODO(Phase 3): handle order submission messages
        pass
