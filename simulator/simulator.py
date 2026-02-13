import asyncio
import json
import random
from datetime import datetime, timezone

import aiocoap
import aiocoap.resource as resource


class GPSResource(resource.Resource):
    async def render_get(self, request):
        # Simule une position proche d'un point fixe (ex: Paris)
        lat = 48.8566 + random.uniform(-0.001, 0.001)
        lon = 2.3522 + random.uniform(-0.001, 0.001)

        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lat": lat,
            "lon": lon,
        }

        return aiocoap.Message(
            payload=json.dumps(payload).encode("utf-8"),
            content_format=50,  # 50 = application/json
        )


async def main():
    site = resource.Site()
    site.add_resource(["gps"], GPSResource())

    await aiocoap.Context.create_server_context(site, bind=("0.0.0.0", 5683))
    print("CoAP GPS simulator listening on udp://0.0.0.0:5683 (/gps)")

    # tourner indéfiniment
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())