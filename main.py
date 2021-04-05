from sanic import Sanic
from sanic.response import json
import asyncio

app = Sanic("Lift app")


@app.websocket('/ws')
async def test(request, ws):
    while True:
        data = "hello!"
        print("Sending: " + data)
        await ws.send(data)
        data = await ws.recv()
        print("Received: " + data)

if __name__ == '__main__':
    app.run()
    exit(0)
