"""
End-to-end tests: talk to the REAL running system through the API Gateway.

These run in GitHub Actions after "docker compose up --build".
To run them on your own machine:

    docker compose up -d --build
    set E2E_BASE_URL=http://localhost:5000        (Windows)
    pytest -m e2e -v
"""
import os

import pytest
import requests

pytestmark = pytest.mark.e2e

BASE = os.environ.get("E2E_BASE_URL", "http://localhost:5000").rstrip("/")


def get(path):
    return requests.get(f"{BASE}{path}", timeout=10)


def post(path, payload):
    return requests.post(f"{BASE}{path}", json=payload, timeout=10)


def test_dashboard_loads():
    r = get("/")
    assert r.status_code == 200
    assert "Microservices Demo" in r.text


def test_all_services_are_up():
    body = get("/gateway/status").json()
    assert set(body) == {"user", "product", "order"}
    for name, info in body.items():
        assert info["status"] == "UP", f"{name} service is not UP: {info}"


def test_users_and_products_are_available():
    users = get("/api/users").json()
    products = get("/api/products").json()
    assert len(users) >= 1
    assert len(products) >= 1


def test_create_user_through_gateway():
    r = post("/api/users", {"name": "CI Student", "email": "ci@example.com"})
    assert r.status_code == 201
    assert r.json()["name"] == "CI Student"


def test_place_order_end_to_end_reduces_stock():
    """Gateway -> Order service -> User service + Product service."""
    product_before = next(p for p in get("/api/products").json() if p["id"] == 101)
    user = get("/api/users").json()[0]

    r = post("/api/orders", {"user_id": user["id"], "product_id": 101, "qty": 2})
    assert r.status_code == 201
    order = r.json()
    assert order["user"] == user["name"]
    assert order["product"] == product_before["name"]
    assert order["total_price"] == product_before["price"] * 2

    product_after = next(p for p in get("/api/products").json() if p["id"] == 101)
    assert product_after["stock"] == product_before["stock"] - 2

    orders = get("/api/orders").json()
    assert any(o["order_id"] == order["order_id"] for o in orders)


def test_order_with_unknown_user_is_rejected():
    r = post("/api/orders", {"user_id": 99999, "product_id": 101, "qty": 1})
    assert r.status_code == 400


def test_order_with_too_large_quantity_is_rejected():
    r = post("/api/orders", {"user_id": 1, "product_id": 101, "qty": 10**6})
    assert r.status_code == 400
