import os
import json
import asyncio
from typing import Dict
import paho.mqtt.client as mqtt

import psycopg2
from psycopg2.extras import RealDictCursor

import aiocoap

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

# =========================
# Config
# =========================
GPS_URI = os.getenv("GPS_URI", "coap://127.0.0.1:5683/gps")
SLOW_INTERVAL = float(os.getenv("SLOW_INTERVAL", "10"))
POLL_INTERVAL = float(os.getenv("GPS_POLL_INTERVAL", "10"))  # secondes
BATTERY_URI = os.getenv("BATTERY_URI", "coap://127.0.0.1:5685/battery")
TEMP_URI = os.getenv("TEMP_URI", "coap://127.0.0.1:5684/temperature")
# =========================
# App + CORS
# =========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

mqtt_client = mqtt.Client()
mqtt_connected = False

# =========================
# DB
# =========================
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "tracking"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "password"),
        cursor_factory=RealDictCursor,
    )


# =========================
# CoAP client helpers
# =========================

def normalize_gps_data(data: dict) -> dict:
    # accepte ts ou timestamp
    ts = data.get("ts") or data.get("timestamp")
    if ts is None:
        raise ValueError("Missing 'ts' or 'timestamp' in GPS payload")

    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        raise ValueError("Missing 'lat' or 'lon' in GPS payload")

    return {"ts": ts, "lat": lat, "lon": lon}

async def fetch_gps_once() -> dict:
    """
    Envoie 1 requête CoAP GET /gps et retourne le JSON décodé.
    """
    protocol = await aiocoap.Context.create_client_context()
    try:
        request = aiocoap.Message(code=aiocoap.GET, uri=GPS_URI)
        response = await protocol.request(request).response
        payload = response.payload.decode("utf-8")
        return json.loads(payload)
    finally:
        await protocol.shutdown()

def insert_gps_point(session_id: int, data: dict):
    """
    Insère un point GPS en BDD.

    data attendu (au minimum) :
      - lat: float/int/str
      - lon: float/int/str
      - ts OU timestamp: str ISO-8601
    """
    lat = data.get("lat")
    lon = data.get("lon")
    ts = data.get("ts") or data.get("timestamp")

    if lat is None or lon is None or ts is None:
        raise ValueError(f"Bad GPS payload for insert: {data}")

    lat = float(lat)
    lon = float(lon)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gps_points (session_id, ts, lat, lon)
                VALUES (%s, %s, %s, %s);
                """,
                (session_id, ts, lat, lon),
            )
        conn.commit()
        
import time

async def gps_polling_loop(session_id: int, stop_event: asyncio.Event):
    last_slow = -SLOW_INTERVAL  # force une lecture dès le démarrage

    while not stop_event.is_set():
        try:
            # GPS (fréquent)
            gps_raw = await coap_get_json(GPS_URI)
            gps = normalize_gps_data(gps_raw)
            insert_gps_point(session_id, gps_raw)
            mqtt_client.publish(
                f"/tracking/{session_id}/gps",
                json.dumps({"session_id": session_id, **gps_raw})
            )

            # Temp + Battery : immédiatement puis toutes les 5 minutes
            now = time.time()
            print(now - last_slow )
            if now - last_slow >= SLOW_INTERVAL:
                last_slow = now
                

                temp_raw = await coap_get_json(TEMP_URI)
                mqtt_client.publish(
                    f"/tracking/{session_id}/temperature",
                    json.dumps({"session_id": session_id, **temp_raw})
                )

                bat_raw = await coap_get_json(BATTERY_URI)
                mqtt_client.publish(
                    f"/tracking/{session_id}/battery",
                    json.dumps({"session_id": session_id, **bat_raw})
                )

        except Exception:
            import traceback
            print(traceback.format_exc())

        try:
            await asyncio.wait_for(stop_event.wait(), timeout= POLL_INTERVAL)
        except asyncio.TimeoutError:
            pass

# =========================
# Gestion des tâches par session
# =========================
session_tasks: Dict[int, asyncio.Task] = {}
session_stop_events: Dict[int, asyncio.Event] = {}


def start_gps_task_for_session(session_id: int):
    """
    Démarre la tâche de polling GPS pour une session si elle n'existe pas déjà.
    """
    if session_id in session_tasks and not session_tasks[session_id].done():
        return

    stop_event = asyncio.Event()
    task = asyncio.create_task(gps_polling_loop(session_id, stop_event))

    session_stop_events[session_id] = stop_event
    session_tasks[session_id] = task


async def stop_gps_task_for_session(session_id: int):
    """
    Stoppe proprement la tâche de polling GPS associée à une session.
    """
    stop_event = session_stop_events.pop(session_id, None)
    task = session_tasks.pop(session_id, None)

    if stop_event:
        stop_event.set()

    if task and not task.done():
        try:
            await task
        except asyncio.CancelledError:
            pass


# =========================
# Routes
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/sessions/{session_id}/gps")
def get_session_gps(session_id: int, limit: int = 5000):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts, lat, lon
                FROM gps_points
                WHERE session_id = %s
                ORDER BY ts ASC
                LIMIT %s;
                """,
                (session_id, limit),
            )
            rows = cur.fetchall()

    return {"session_id": session_id, "points": rows}

class StartSessionIn(BaseModel):
    nom: str = Field(min_length=1)
    prenom: str = Field(min_length=1)
    email: str = Field(min_length=3)


@app.post("/sessions/start")
async def start_session(payload: StartSessionIn):
    # 1) vérifier que l'utilisateur existe + créer la session
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, nom, prenom, email
                FROM users
                WHERE nom = %s AND prenom = %s AND email = %s
                LIMIT 1;
                """,
                (payload.nom, payload.prenom, payload.email),
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(
    status_code=404,
    detail="L'utilisateur n'existe pas dans la BDD. Veuillez essayer avec : Raab Dyhia dyhia@gmail.com"
)

            cur.execute(
                """
                INSERT INTO sessions (user_id, status, end_time)
                VALUES (%s, 'running', NULL)
                RETURNING id, user_id, start_time, end_time, status;
                """,
                (user["id"],),
            )
            session = cur.fetchone()

        conn.commit()

    session_id = int(session["id"])

    # 2) démarrer le polling CoAP immédiatement pour cette session
    start_gps_task_for_session(session_id)

    return {
        "session_id": session_id,
        "user_id": session["user_id"],
        "start_time": session["start_time"],
        "end_time": session["end_time"],
        "status": session["status"],
    }




@app.get("/users/{user_id}/sessions")
def list_user_sessions(user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            # optionnel: vérifier que le user existe
            cur.execute("SELECT id FROM users WHERE id=%s;", (user_id,))
            u = cur.fetchone()
            if not u:
                raise HTTPException(status_code=404, detail="User not found")

            cur.execute(
                """
                SELECT id, start_time, end_time, status
                FROM sessions
                WHERE user_id = %s
                ORDER BY start_time DESC;
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    # rows est déjà une liste de dicts avec RealDictCursor
    return {"user_id": user_id, "sessions": rows}
@app.post("/sessions/{session_id}/stop")
async def stop_session(session_id: int):
    # 1) arrêter le polling CoAP
    await stop_gps_task_for_session(session_id)

    # 2) stop session en BDD
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                SET status='stopped', end_time=now()
                WHERE id=%s
                RETURNING id, user_id, start_time, end_time, status;
                """,
                (session_id,),
            )
            session = cur.fetchone()
        conn.commit()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": int(session["id"]),
        "user_id": session["user_id"],
        "start_time": session["start_time"],
        "end_time": session["end_time"],
        "status": session["status"],
    }

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = (rc == 0)
    print("MQTT connected" if mqtt_connected else f"MQTT connect failed rc={rc}")

mqtt_client.on_connect = on_connect

@app.on_event("startup")
def startup_mqtt():
    # connexion non bloquante
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
    
@app.on_event("shutdown")
def shutdown_mqtt():
    try:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except Exception:
        pass


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    # 1) arrêter la tâche de polling (si elle existe)
    await stop_gps_task_for_session(session_id)

    # 2) supprimer la session
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE id=%s RETURNING id;", (session_id,))
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"deleted_session_id": session_id}
@app.get("/debug/gps")
async def debug_gps():
    """
    Endpoint utile pour tester que le backend arrive à joindre le simulateur CoAP.
    """
    try:
        return await fetch_gps_once()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
def normalize_gps_payload(raw: dict) -> dict:
    lat = raw.get("lat")
    lon = raw.get("lon")
    ts = raw.get("ts") or raw.get("timestamp")

    if lat is None or lon is None or ts is None:
        raise ValueError(f"Bad GPS payload: {raw}")

    return {"lat": float(lat), "lon": float(lon), "ts": ts}   
    
async def coap_get_json(uri: str) -> dict:
    protocol = await aiocoap.Context.create_client_context()
    try:
        req = aiocoap.Message(code=aiocoap.GET, uri=uri)
        resp = await protocol.request(req).response

        raw = resp.payload.decode("utf-8", errors="replace")
        print(f"CoAP DEBUG uri={uri} code={resp.code} raw={raw!r}")

        if not raw.strip():
            raise ValueError(f"Empty CoAP payload (code={resp.code}) from {uri}")

        if not str(resp.code).startswith("2."):
            raise ValueError(f"CoAP error {resp.code} from {uri}: {raw}")

        return json.loads(raw)
    finally:
        await protocol.shutdown()