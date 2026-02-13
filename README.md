# Thread Lab (OpenThread + CoAP sensors)

## Prérequis
- Docker + Docker Compose

## Lancer
```bash
cd thread-lab
docker compose up -d --build
docker ps

## 🌍 Network

This project uses **IPv6 internally** because OpenThread (Thread protocol) requires IPv6.

- Thread mesh network → IPv6
- Local CoAP tests → 127.0.0.1 (Docker host network)

