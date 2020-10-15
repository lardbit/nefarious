"""
ASGI config for nefarious project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/

Using Starlette for Routing and WebSockets
https://www.starlette.io/websockets/
"""
import os
import logging
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
        # send to all websocket connections
        for ws in self.websockets:
            try:
                await ws.send_json(data)
            # failed communicating with this websocket so remove it from the pool
            except Exception as e:
                logging.exception(e)
                self.websockets.remove(websocket)

    async def on_disconnect(self, websocket, close_code):
        if websocket in self.websockets:
            logging.info('removing disconnected websocket')
            self.websockets.remove(websocket)
        else:
            logging.info('disconnected websocket not found')


application = Starlette(
    routes=[
        # websockets
        WebSocketRoute("/ws", endpoint=WS),
        # django
        Route("/{any:path}", endpoint=get_asgi_application()),
    ]
)
