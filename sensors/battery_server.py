import asyncio
import os
import random
from aiocoap import *
from aiocoap.resource import Resource, Site

class BatteryResource(Resource):
    async def render_get(self, request):
        level = random.randint(40, 100)
        return Message(payload=f'{{"battery": {level}}}'.encode())

async def main():
    root = Site()
    root.add_resource(['battery'], BatteryResource())

    PORT = int(os.environ.get("COAP_PORT", "5683"))
    await Context.create_server_context(root, bind=("::", PORT))

    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
