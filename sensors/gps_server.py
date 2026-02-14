import json, datetime, random, asyncio
from aiocoap import resource, Context, Message
from aiocoap.numbers.codes import Code

class GPS(resource.Resource):
    async def render_get(self, request):
        payload = {
            "lat": round(48.2500 + random.uniform(-0.01, 0.01), 6),
            "lon": round(4.0200  + random.uniform(-0.01, 0.01), 6),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        return Message(code=Code.CONTENT, payload=json.dumps(payload).encode())

async def main():
    root = resource.Site()
    root.add_resource(['gps'], GPS())
    import os
    PORT = int(os.environ.get("COAP_PORT", "5683"))
    await Context.create_server_context(root, bind=("::", PORT))
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
