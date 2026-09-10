"""
API GATEWAY
Port: 5000
Responsibility: SINGLE entry point for the outside world (browser / frontend).
It forwards requests to the correct backend microservice.
This is the standard "API Gateway pattern" used in real microservices systems
(clients never talk to individual services directly).
"""

import os
from flask import Flask, jsonify, request, send_from_directory
import requests

app = Flask(__name__, static_folder="static")

# Defaults keep working for "python api_gateway.py" on a single machine.
# In Docker, docker-compose sets these to the service names instead
# (e.g. http://user-service:5002) so containers can find each other.
SERVICES = {
    "user": os.environ.get("USER_SERVICE_URL", "http://127.0.0.1:5002"),
    "product": os.environ.get("PRODUCT_SERVICE_URL", "http://127.0.0.1:5001"),
    "order": os.environ.get("ORDER_SERVICE_URL", "http://127.0.0.1:5003"),
}


@app.route("/")
def dashboard():
    return send_from_directory("static", "index.html")


@app.route("/gateway/status", methods=["GET"])
def status():
    """Check health of every microservice - great for live demo."""
    results = {}
    for name, base_url in SERVICES.items():
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            results[name] = r.json()
        except requests.exceptions.ConnectionError:
            results[name] = {"service": f"{name}-service", "status": "DOWN"}
    return jsonify(results)


# ---------- Routes forwarded to USER SERVICE ----------
@app.route("/api/users", methods=["GET", "POST"])
def users():
    if request.method == "GET":
        r = requests.get(f"{SERVICES['user']}/users")
    else:
        r = requests.post(f"{SERVICES['user']}/users", json=request.get_json())
    return jsonify(r.json()), r.status_code


# ---------- Routes forwarded to PRODUCT SERVICE ----------
@app.route("/api/products", methods=["GET"])
def products():
    r = requests.get(f"{SERVICES['product']}/products")
    return jsonify(r.json()), r.status_code


# ---------- Routes forwarded to ORDER SERVICE ----------
@app.route("/api/orders", methods=["GET", "POST"])
def orders():
    if request.method == "GET":
        r = requests.get(f"{SERVICES['order']}/orders")
    else:
        r = requests.post(f"{SERVICES['order']}/orders", json=request.get_json())
    return jsonify(r.json()), r.status_code


if __name__ == "__main__":
    print("Starting API GATEWAY on http://127.0.0.1:5000")
    print("Open this URL in your browser to see the demo dashboard.")
    app.run(host="0.0.0.0", port=5000, debug=False)
