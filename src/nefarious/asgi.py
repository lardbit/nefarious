"""
ASGI config for nefarious project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/

Using Starlette for Routing and WebSockets
https://www.starlette.io/websockets/
"""
import os
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.endpoints import WebSocketEndpoint
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nefarious.settings')


class WS(WebSocketEndpoint):
    encoding = 'text'
    websockets = []

    async def on_connect(self, websocket):
        await websocket.accept()
        self.websockets.append(websocket)

    async def on_receive(self, websocket, data):
        [await ws.send_text(f"Message text was: {data}") for ws in self.websockets]

    async def on_disconnect(self, websocket, close_code):
        pass


application = Starlette(
    routes=[
        Route("/", get_asgi_application()),
        WebSocketRoute("/ws", WS),
    ]
)
