import json, datetime, asyncio, os, time, random
from aiocoap import resource, Context, Message
from aiocoap.numbers.codes import Code

class Battery(resource.Resource):
    def __init__(self):
        super().__init__()
        self.level = 95.0
        self.last = time.monotonic()
        self.drain_per_sec = 1.0 / (2* 60)  # 1% toutes les 10 minutes

    def step(self):
        now = time.monotonic()
        dt = now - self.last
        self.last = now

        drain = dt * self.drain_per_sec
        noise = random.uniform(-0.05, 0.05)

        new_level = self.level - drain + noise

        # batterie ne doit pas monter pendant une course
        self.level = min(self.level, new_level)

        # bornes
        self.level = max(0.0, min(100.0, self.level))

    async def render_get(self, request):
        self.step()
        payload = {
            "battery": int(round(self.level)),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        return Message(code=Code.CONTENT, payload=json.dumps(payload).encode(), content_format=50)

async def main():
    root = resource.Site()
    root.add_resource(["battery"], Battery())
    port = int(os.environ.get("COAP_PORT", "5685"))
    await Context.create_server_context(root, bind=("::", port))
    print(f"Battery CoAP server on udp://[::]:{port} (/battery)")
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
