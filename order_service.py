"""
ORDER SERVICE
Port: 5003
Responsibility: Create/manage orders.
KEY CONCEPT FOR DEMO: This service does NOT have its own copy of user or
product data. It calls USER SERVICE and PRODUCT SERVICE over HTTP to get
that information - this is service-to-service communication, the heart
of microservices architecture.
"""

import os
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Defaults keep working for "python order_service.py" on a single machine.
# docker-compose overrides these with the service names.
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://127.0.0.1:5002")
PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://127.0.0.1:5001")

ORDERS = {}
next_order_id = 1


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "order-service", "status": "UP", "port": 5003})


@app.route("/orders", methods=["GET"])
def get_all_orders():
    return jsonify(list(ORDERS.values()))


@app.route("/orders", methods=["POST"])
def create_order():
    global next_order_id
    data = request.get_json()
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    qty = data.get("qty", 1)

    # 1. Validate user by calling USER SERVICE
    try:
        user_resp = requests.get(f"{USER_SERVICE_URL}/users/{user_id}", timeout=5)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "User Service is DOWN. Start user_service.py"}), 503

    if user_resp.status_code != 200:
        return jsonify({"error": "Invalid user_id"}), 400
    user = user_resp.json()

    # 2. Validate product by calling PRODUCT SERVICE
    try:
        product_resp = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Product Service is DOWN. Start product_service.py"}), 503

    if product_resp.status_code != 200:
        return jsonify({"error": "Invalid product_id"}), 400
    product = product_resp.json()

    if product["stock"] < qty:
        return jsonify({"error": "Not enough stock"}), 400

    # 3. Reduce stock by calling PRODUCT SERVICE again
    requests.post(f"{PRODUCT_SERVICE_URL}/products/{product_id}/reduce_stock", json={"qty": qty})

    # 4. Create the order locally
    order = {
        "order_id": next_order_id,
        "user": user["name"],
        "product": product["name"],
        "qty": qty,
        "total_price": product["price"] * qty,
    }
    ORDERS[next_order_id] = order
    next_order_id += 1

    return jsonify(order), 201


if __name__ == "__main__":
    print("Starting ORDER SERVICE on http://127.0.0.1:5003")
    app.run(host="0.0.0.0", port=5003, debug=False)
