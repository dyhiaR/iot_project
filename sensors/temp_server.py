import json, datetime, asyncio, os, random
from aiocoap import resource, Context, Message
from aiocoap.numbers.codes import Code

class Temperature(resource.Resource):
    def __init__(self):
        super().__init__()
        self.temp = random.uniform(10.0, 24.0)
        self.target = self.temp + random.uniform(-0.5, 0.5)              # valeur initiale
                    
        self.alpha = 0.05               # inertie (plus petit = plus lent)

    def step(self):
        # fait varier la cible très doucement (ex: +/- 0.02°C)
        self.target += random.uniform(-0.02, 0.02)
        self.target = max(15.0, min(30.0, self.target))  # bornes plausibles

        noise = random.uniform(-0.10, 0.10)              # petit bruit
        self.temp = self.temp + self.alpha * (self.target - self.temp) + noise
        self.temp = max(-10.0, min(50.0, self.temp))      # sécurité

    async def render_get(self, request):
        self.step()
        payload = {
            "temperature": round(self.temp, 1),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        return Message(code=Code.CONTENT, payload=json.dumps(payload).encode(), content_format=50)

async def main():
    root = resource.Site()
    root.add_resource(["temperature"], Temperature())
    port = int(os.environ.get("COAP_PORT", "5684"))
    await Context.create_server_context(root, bind=("::", port))
    print(f"Temperature CoAP server on udp://[::]:{port} (/temperature)")
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
