"""
PRODUCT SERVICE
Port: 5001
Responsibility: Manage product catalog ONLY.
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

PRODUCTS = {
    101: {"id": 101, "name": "Laptop Bag",     "price": 899,  "stock": 25},
    102: {"id": 102, "name": "Wireless Mouse", "price": 499,  "stock": 50},
    103: {"id": 103, "name": "USB Keyboard",   "price": 799,  "stock": 30},
    104: {"id": 104, "name": "Notebook",       "price": 60,   "stock": 200},
    105: {"id": 105, "name": "Pen Drive 32GB", "price": 350, "stock": 40},
    106: {"id": 105, "name": "Pen Drive 32GB", "price": 350, "stock": 40},
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "product-service", "status": "UP", "port": 5001})


@app.route("/products", methods=["GET"])
def get_all_products():
    return jsonify(list(PRODUCTS.values()))


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = PRODUCTS.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@app.route("/products/<int:product_id>/reduce_stock", methods=["POST"])
def reduce_stock(product_id):
    data = request.get_json()
    qty = data.get("qty", 1)
    product = PRODUCTS.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product["stock"] < qty:
        return jsonify({"error": "Insufficient stock"}), 400
    product["stock"] -= qty
    return jsonify(product)


if __name__ == "__main__":
    print("Starting PRODUCT SERVICE on http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
