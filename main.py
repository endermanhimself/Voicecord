import os
import sys
import json
import time
import signal
import threading
import requests
from websocket import WebSocket, WebSocketConnectionClosedException
from keep_alive import keep_alive

# ================= CONFIG =================
status = "online"

GUILD_ID = "1318279473912610816"
CHANNEL_ID = "1466124838170136740"
SELF_MUTE = True
SELF_DEAF = False

RECONNECT_DELAY = 180  # 3 minutes (prevents reconnect storms)
# ==========================================

RUNNING = True

def shutdown_handler(sig, frame):
    global RUNNING
    print("Shutting down cleanly...")
    RUNNING = False

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if os.getenv("ENABLE_JOINER") != "true":
    print("Joiner disabled via env variable.")
    sys.exit()

token = os.getenv("TOKEN")
if not token:
    print("TOKEN missing.")
    sys.exit()

headers = {
    "Authorization": token,
    "Content-Type": "application/json"
}

r = requests.get(
    "https://canary.discordapp.com/api/v9/users/@me",
    headers=headers
)

if r.status_code != 200:
    print("Invalid token.")
    sys.exit()

user = r.json()
print(f"Logged in as {user['username']}#{user['discriminator']} ({user['id']})")

def heartbeat(ws, interval):
    while RUNNING:
        time.sleep(interval)
        try:
            ws.send(json.dumps({"op": 1, "d": None}))
        except WebSocketConnectionClosedException:
            break

def join_once():
    ws = WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")

    hello = json.loads(ws.recv())
    hb_interval = hello["d"]["heartbeat_interval"] / 1000

    identify = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "windows",
                "$browser": "chrome",
                "$device": "pc"
            },
            "presence": {
                "status": status,
                "afk": False
            }
        }
    }

    voice = {
        "op": 4,
        "d": {
            "guild_id": GUILD_ID,
            "channel_id": CHANNEL_ID,
            "self_mute": SELF_MUTE,
            "self_deaf": SELF_DEAF
        }
    }

    ws.send(json.dumps(identify))
    ws.send(json.dumps(voice))

    threading.Thread(
        target=heartbeat,
        args=(ws, hb_interval),
        daemon=True
    ).start()

    while RUNNING:
        ws.recv()

    try:
        ws.close()
    except Exception:
        pass

def main():
    while RUNNING:
        try:
            join_once()
        except Exception as e:
            print("Disconnected:", e)

        if RUNNING:
            print(f"Waiting {RECONNECT_DELAY}s before reconnect...")
            time.sleep(RECONNECT_DELAY)

keep_alive()
main()
