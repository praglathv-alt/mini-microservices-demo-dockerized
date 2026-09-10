"""
USER SERVICE
Port: 5002
Responsibility: Manage user data ONLY.
This is a standalone microservice - it knows nothing about products or orders.
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory "database" (simple dict, no real DB needed for demo)
USERS = {
    1: {"id": 1, "name": "Kishore", "email": "arun@example.com"},
    2: {"id": 2, "name": "Divya S",    "email": "divya@example.com"},
    3: {"id": 3, "name": "Karthik R",  "email": "karthik@example.com"},
    4: {"id": 4, "name": "Pragalath V",  "email": "praglath.v@egspec.org"},
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "user-service", "status": "UP", "port": 5002})


@app.route("/users", methods=["GET"])
def get_all_users():
    return jsonify(list(USERS.values()))


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    new_id = max(USERS.keys()) + 1
    USERS[new_id] = {"id": new_id, "name": data.get("name"), "email": data.get("email")}
    return jsonify(USERS[new_id]), 201


if __name__ == "__main__":
    print("Starting USER SERVICE on http://127.0.0.1:5002")
    app.run(host="0.0.0.0", port=5002, debug=False)
