"""
Unit tests for ORDER SERVICE (port 5003).

The order service calls the USER and PRODUCT services over HTTP.
In a unit test we do NOT start those services - we replace requests.get /
requests.post with fakes that return whatever the test needs. This is
called "mocking", and it keeps the tests fast and independent.
"""
import pytest
import requests


USER = {"id": 1, "name": "Kishore", "email": "k@example.com"}
PRODUCT = {"id": 101, "name": "Laptop Bag", "price": 100, "stock": 10}


@pytest.fixture
def backends(monkeypatch, fake_response):
    """Fake USER + PRODUCT services. Returns a dict to inspect/adjust."""
    state = {"user": USER, "product": PRODUCT, "posts": [], "gets": []}

    def fake_get(url, **kwargs):
        state["gets"].append(url)
        if "/users/" in url:
            return fake_response(state["user"], 200) if state["user"] else fake_response({"error": "x"}, 404)
        if "/products/" in url:
            return fake_response(state["product"], 200) if state["product"] else fake_response({"error": "x"}, 404)
        raise AssertionError(f"unexpected GET {url}")

    def fake_post(url, **kwargs):
        state["posts"].append((url, kwargs.get("json")))
        return fake_response({}, 200)

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)
    return state


def test_health_is_up(order_client):
    r = order_client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["service"] == "order-service"
    assert r.get_json()["status"] == "UP"


def test_orders_start_empty(order_client):
    assert order_client.get("/orders").get_json() == []


def test_create_order_success(order_client, backends):
    r = order_client.post("/orders", json={"user_id": 1, "product_id": 101, "qty": 2})
    assert r.status_code == 201
    order = r.get_json()
    assert order["order_id"] == 1
    assert order["user"] == "Kishore"
    assert order["product"] == "Laptop Bag"
    assert order["qty"] == 2
    assert order["total_price"] == 200  # 100 x 2


def test_create_order_asks_product_service_to_reduce_stock(order_client, order_module, backends):
    order_client.post("/orders", json={"user_id": 1, "product_id": 101, "qty": 4})
    assert backends["posts"] == [
        (f"{order_module.PRODUCT_SERVICE_URL}/products/101/reduce_stock", {"qty": 4})
    ]


def test_create_order_calls_user_then_product_service(order_client, order_module, backends):
    order_client.post("/orders", json={"user_id": 1, "product_id": 101})
    assert backends["gets"] == [
        f"{order_module.USER_SERVICE_URL}/users/1",
        f"{order_module.PRODUCT_SERVICE_URL}/products/101",
    ]


def test_qty_defaults_to_one(order_client, backends):
    r = order_client.post("/orders", json={"user_id": 1, "product_id": 101})
    assert r.status_code == 201
    assert r.get_json()["qty"] == 1
    assert r.get_json()["total_price"] == 100


def test_order_ids_increase_and_orders_are_listed(order_client, backends):
    order_client.post("/orders", json={"user_id": 1, "product_id": 101})
    second = order_client.post("/orders", json={"user_id": 1, "product_id": 101})
    assert second.get_json()["order_id"] == 2
    listed = order_client.get("/orders").get_json()
    assert [o["order_id"] for o in listed] == [1, 2]


def test_invalid_user_is_rejected(order_client, backends):
    backends["user"] = None  # user service answers 404
    r = order_client.post("/orders", json={"user_id": 999, "product_id": 101})
    assert r.status_code == 400
    assert r.get_json()["error"] == "Invalid user_id"
    assert backends["posts"] == []


def test_invalid_product_is_rejected(order_client, backends):
    backends["product"] = None  # product service answers 404
    r = order_client.post("/orders", json={"user_id": 1, "product_id": 999})
    assert r.status_code == 400
    assert r.get_json()["error"] == "Invalid product_id"
    assert backends["posts"] == []


def test_not_enough_stock_is_rejected_and_stock_not_reduced(order_client, backends):
    r = order_client.post("/orders", json={"user_id": 1, "product_id": 101, "qty": 11})
    assert r.status_code == 400
    assert r.get_json()["error"] == "Not enough stock"
    assert backends["posts"] == []
    assert order_client.get("/orders").get_json() == []


def test_user_service_down_returns_503(order_client, monkeypatch):
    def boom(url, **kwargs):
        raise requests.exceptions.ConnectionError("user service is down")

    monkeypatch.setattr(requests, "get", boom)
    r = order_client.post("/orders", json={"user_id": 1, "product_id": 101})
    assert r.status_code == 503
    assert "User Service is DOWN" in r.get_json()["error"]


def test_product_service_down_returns_503(order_client, monkeypatch, fake_response):
    def fake_get(url, **kwargs):
        if "/users/" in url:
            return fake_response(USER, 200)
        raise requests.exceptions.ConnectionError("product service is down")

    monkeypatch.setattr(requests, "get", fake_get)
    r = order_client.post("/orders", json={"user_id": 1, "product_id": 101})
    assert r.status_code == 503
    assert "Product Service is DOWN" in r.get_json()["error"]
