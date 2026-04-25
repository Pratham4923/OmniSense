import os
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request, send_from_directory

from utils.mock_data import (
    BASE_DIR,
    get_acoustic_data,
    get_green_wave_path,
    get_rfid_data,
    get_system_history,
    get_traffic_metrics,
    get_vision_data,
)


app = Flask(__name__)

STATE = {
    "sim_running": False,
    "emergency_type": None,
    "countdown": 30,
    "junction_index": 0,
    "last_tick": time.time(),
    "preempt_until": 0.0,
}
STATE_LOCK = threading.Lock()


def ist_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S UTC+05:30")


def normalize_media_path(path):
    if not path:
        return None
    relative_path = os.path.relpath(path, BASE_DIR).replace("\\", "/")
    return f"/media/{relative_path}"


def advance_state(now):
    if not STATE["sim_running"]:
        STATE["last_tick"] = now
        return

    if STATE["emergency_type"] and STATE["preempt_until"] and now >= STATE["preempt_until"]:
        STATE["emergency_type"] = None
        STATE["preempt_until"] = 0.0
        STATE["junction_index"] = (STATE["junction_index"] + 1) % len(get_green_wave_path())
        STATE["countdown"] = 30
        STATE["last_tick"] = now

    if STATE["preempt_until"]:
        return

    elapsed = int(now - STATE["last_tick"])
    if elapsed <= 0:
        return

    STATE["countdown"] -= elapsed
    while STATE["countdown"] <= 0:
        STATE["countdown"] += 30
        STATE["junction_index"] = (STATE["junction_index"] + 1) % len(get_green_wave_path())

    STATE["last_tick"] = now


def compose_payload():
    now = time.time()
    with STATE_LOCK:
        advance_state(now)
        emergency_type = STATE["emergency_type"]
        sim_running = STATE["sim_running"]
        countdown = STATE["countdown"]
        junction_index = STATE["junction_index"]
        preempt_until = STATE["preempt_until"]

    rfid = get_rfid_data(emergency_type)
    acoustic = get_acoustic_data(emergency_type)
    vision = get_vision_data(emergency_type)
    junctions = get_green_wave_path()
    metrics = get_traffic_metrics()
    history = get_system_history()

    is_preempted = bool(emergency_type and preempt_until and preempt_until > now)

    return {
        "clock": ist_time(),
        "simRunning": sim_running,
        "emergencyType": emergency_type,
        "countdown": countdown,
        "junctionIndex": junction_index,
        "junctions": junctions,
        "metrics": metrics,
        "history": history,
        "rfid": rfid,
        "acoustic": {
            **acoustic,
            "audioUrl": normalize_media_path(acoustic.get("audio_path")),
        },
        "vision": {
            **vision,
            "imageUrl": normalize_media_path(vision.get("image_path")),
        },
        "isPreempted": is_preempted,
        "signalState": "GREEN" if is_preempted else ("YELLOW" if countdown <= 5 else "RED"),
        "activeSector": junctions[junction_index]["id"],
    }


@app.route("/")
def index():
    return render_template("index.html", initial_state=compose_payload())


@app.route("/api/state")
def api_state():
    return jsonify(compose_payload())


@app.route("/api/action", methods=["POST"])
def api_action():
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")

    with STATE_LOCK:
        now = time.time()
        advance_state(now)

        if action == "toggle":
            STATE["sim_running"] = not STATE["sim_running"]
            STATE["last_tick"] = now
        elif action == "inject":
            vehicle_type = payload.get("vehicleType")
            if vehicle_type in {"Ambulance", "Firetruck"}:
                STATE["sim_running"] = True
                STATE["emergency_type"] = vehicle_type
                STATE["preempt_until"] = now + 3
                STATE["last_tick"] = now
        elif action == "reset":
            STATE["sim_running"] = False
            STATE["emergency_type"] = None
            STATE["countdown"] = 30
            STATE["junction_index"] = 0
            STATE["preempt_until"] = 0.0
            STATE["last_tick"] = now

    return jsonify(compose_payload())


@app.route("/media/<path:relative_path>")
def media(relative_path):
    return send_from_directory(BASE_DIR, relative_path)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
