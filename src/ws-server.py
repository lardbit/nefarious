import asyncio
import logging
import websockets

logging.basicConfig()

USERS = set()


async def notify_state(message):
    if USERS:  # asyncio.wait doesn't accept an empty list
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    USERS.add(websocket)


async def unregister(websocket):
    USERS.remove(websocket)


async def handle(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            logging.warning(message)
            await notify_state(message)
    finally:
        await unregister(websocket)


start_server = websockets.serve(handle, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
