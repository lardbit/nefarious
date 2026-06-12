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
from starlette.websockets import WebSocket
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nefarious.settings')

websockets_pool = []


async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    websockets_pool.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # send to all websocket connections
            for ws in websockets_pool[:]:
                try:
                    await ws.send_json(data)
                except Exception as e:
                    logging.exception(e)
                    if ws in websockets_pool:
                        websockets_pool.remove(ws)
    except Exception:
        pass
    finally:
        if websocket in websockets_pool:
            logging.info('removing disconnected websocket')
            websockets_pool.remove(websocket)
        else:
            logging.info('disconnected websocket not found')


application = Starlette(
    routes=[
        WebSocketRoute("/ws", endpoint=ws_endpoint),
        Route("/{any:path}", endpoint=get_asgi_application()),
    ]
)
