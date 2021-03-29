from sanic import Sanic
from sanic.response import json
import asyncio

app = Sanic("Lift app")


@app.route('/')
async def test(request):
    return json({'lift': 'ok'})

if __name__ == '__main__':
    app.run()
