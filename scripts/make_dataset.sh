#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# démarre seulement gps
docker compose up -d --build gps

HEX="$(docker exec -i th-gps bash -lc '
OTCLI="/opt/openthread/build/posix/src/posix/ot-cli"
printf "dataset init new\ndataset commit active\ndataset active -x\n" | "$OTCLI"
' | tail -n 1 | tr -d "\r")"

if [ -z "$HEX" ]; then
  echo "❌ Dataset vide"
  exit 1
fi

echo "$HEX" > scripts/dataset.hex
echo "✅ Dataset écrit dans scripts/dataset.hex: $HEX"

docker compose stop gps
