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


# =========================
# Config
# =========================
GPS_URI = os.getenv("GPS_URI", "coap://simulator/gps")
POLL_INTERVAL = float(os.getenv("GPS_POLL_INTERVAL", "10"))  # secondes


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
        user=os.getenv("DB_USER", "tracking"),
        password=os.getenv("DB_PASSWORD", "tracking"),
        cursor_factory=RealDictCursor,
    )


# =========================
# CoAP client helpers
# =========================
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


async def gps_polling_loop(session_id: int, stop_event: asyncio.Event):
    """
    Boucle qui tourne tant que stop_event n'est pas set().
    """
    while not stop_event.is_set():
        try:
            data = await fetch_gps_once()
            print(f"[session {session_id}] GPS =", data)
            topic = f"/tracking/{session_id}/gps"
            payload = json.dumps({ "session_id": session_id, **data})


            mqtt_client.publish(topic, payload)
            # TODO prochaine étape: insérer en BDD dans gps_points(session_id, ts, lat, lon)
        except Exception as e:
            print(f"[session {session_id}] GPS polling error:", repr(e))

        # Attend soit l'intervalle, soit un stop immédiat
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL)
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
                raise HTTPException(status_code=404, detail="User not found")

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


@app.get("/debug/gps")
async def debug_gps():
    """
    Endpoint utile pour tester que le backend arrive à joindre le simulateur CoAP.
    """
    try:
        return await fetch_gps_once()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))