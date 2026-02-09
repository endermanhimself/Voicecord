import os
import sys
import json
import time
import threading
import requests
from websocket import WebSocket
from keep_alive import keep_alive

status = "online"  # online / dnd / idle

GUILD_ID = "PUT_GUILD_ID_HERE"
CHANNEL_ID = "PUT_CHANNEL_ID_HERE"
SELF_MUTE = True
SELF_DEAF = False

usertoken = os.getenv("TOKEN")
if not usertoken:
    print("[ERROR] TOKEN not found in environment variables.")
    sys.exit()

headers = {
    "Authorization": usertoken,
    "Content-Type": "application/json"
}

validate = requests.get(
    "https://canary.discordapp.com/api/v9/users/@me",
    headers=headers
)

if validate.status_code != 200:
    print("[ERROR] Invalid token.")
    sys.exit()

userinfo = validate.json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

def heartbeat_loop(ws, interval):
    while True:
        time.sleep(interval)
        ws.send(json.dumps({"op": 1, "d": None}))

def joiner(token, status):
    ws = WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")

    hello = json.loads(ws.recv())
    heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000

    auth = {
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

    vc = {
        "op": 4,
        "d": {
            "guild_id": GUILD_ID,
            "channel_id": CHANNEL_ID,
            "self_mute": SELF_MUTE,
            "self_deaf": SELF_DEAF
        }
    }

    ws.send(json.dumps(auth))
    ws.send(json.dumps(vc))

    threading.Thread(
        target=heartbeat_loop,
        args=(ws, heartbeat_interval),
        daemon=True
    ).start()

    while True:
        ws.recv()

def run_joiner():
    print(f"Logged in as {username}#{discriminator} ({userid})")
    while True:
        try:
            joiner(usertoken, status)
        except Exception as e:
            print("Disconnected, reconnecting...", e)
            time.sleep(5)

keep_alive()
run_joiner()
