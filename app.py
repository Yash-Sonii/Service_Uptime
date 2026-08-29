"""
Service Uptime Monitor
-----------------------
A small Flask app that checks the availability of a list of services on a
background thread and exposes their live status through a JSON API and a
simple auto-refreshing dashboard.
"""

import threading
import time
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Services to watch. Add/remove URLs here.
SERVICES = [
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://github.com"},
    {"name": "Log Dashboard It is the dummy ", "url": "https://httpbin.in/status/200"},
]

CHECK_INTERVAL_SECONDS = 30

# In-memory store of the latest status for each service
status_store = {}
store_lock = threading.Lock()


def check_service(service):
    start = time.time()
    try:
        response = requests.get(service["url"], timeout=5)
        elapsed_ms = round((time.time() - start) * 1000, 1)
        return {
            "name": service["name"],
            "url": service["url"],
            "up": response.status_code < 400,
            "status_code": response.status_code,
            "response_ms": elapsed_ms,
            "checked_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        }
    except requests.RequestException:
        elapsed_ms = round((time.time() - start) * 1000, 1)
        return {
            "name": service["name"],
            "url": service["url"],
            "up": False,
            "status_code": None,
            "response_ms": elapsed_ms,
            "checked_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        }


def background_checker():
    while True:
        for service in SERVICES:
            result = check_service(service)
            with store_lock:
                status_store[service["name"]] = result
        time.sleep(CHECK_INTERVAL_SECONDS)


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/status")
def status():
    with store_lock:
        return jsonify(list(status_store.values()))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    checker_thread = threading.Thread(target=background_checker, daemon=True)
    checker_thread.start()
    app.run(host="0.0.0.0", port=8089)