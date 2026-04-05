import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/caca/1"
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                msg = await websocket.recv()
                print("RECEIVED:", msg)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(test_ws())
