#!/usr/bin/env bash
set -e

# ROLE = arg1 sinon env ROLE sinon gps
ROLE="${1:-${ROLE:-gps}}"

# Ports différents (obligatoire si network_mode: host)
case "$ROLE" in
  gps) COAP_PORT=5683 ;;
  temperature) COAP_PORT=5684 ;;
  battery) COAP_PORT=5685 ;;
  *) echo "ROLE inconnu: $ROLE"; exit 2 ;;
esac

export COAP_PORT
echo "== start_sensor ROLE=$ROLE PORT=$COAP_PORT =="

# (Pour l'instant on fait JUSTE la couche capteur CoAP)
case "$ROLE" in
  gps)         exec python3 /work/sensors/gps_server.py ;;
  temperature) exec python3 /work/sensors/temp_server.py ;;
  battery)     exec python3 /work/sensors/battery_server.py ;;
esac
