"""
Unit tests for API GATEWAY (port 5000).

The gateway only forwards requests to the other services, so these tests
mock requests.get / requests.post and check that the gateway calls the
right URL and passes the answer back unchanged.
"""
import pytest
import requests


def test_dashboard_page_is_served(gateway_client):
    r = gateway_client.get("/")
    try:
        assert r.status_code == 200
        assert b"Microservices Demo" in r.data
    finally:
        r.close()


def test_status_all_services_up(gateway_client, monkeypatch, fake_response):
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: fake_response({"service": url, "status": "UP"}, 200),
    )
    r = gateway_client.get("/gateway/status")
    assert r.status_code == 200
    body = r.get_json()
    assert set(body) == {"user", "product", "order"}
    assert all(v["status"] == "UP" for v in body.values())


def test_status_shows_down_service(gateway_client, gateway_module, monkeypatch, fake_response):
    user_url = gateway_module.SERVICES["user"]

    def fake_get(url, **kw):
        if url.startswith(user_url):
            raise requests.exceptions.ConnectionError("down")
        return fake_response({"status": "UP"}, 200)

    monkeypatch.setattr(requests, "get", fake_get)
    body = gateway_client.get("/gateway/status").get_json()
    assert body["user"]["status"] == "DOWN"
    assert body["product"]["status"] == "UP"
    assert body["order"]["status"] == "UP"


def test_status_checks_the_health_endpoint_of_each_service(gateway_client, gateway_module, monkeypatch, fake_response):
    seen = []
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: seen.append(url) or fake_response({"status": "UP"}, 200),
    )
    gateway_client.get("/gateway/status")
    assert sorted(seen) == sorted(f"{u}/health" for u in gateway_module.SERVICES.values())


def test_get_users_is_forwarded(gateway_client, gateway_module, monkeypatch, fake_response):
    calls = []
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: calls.append(url) or fake_response([{"id": 1}], 200),
    )
    r = gateway_client.get("/api/users")
    assert r.status_code == 200
    assert r.get_json() == [{"id": 1}]
    assert calls == [f"{gateway_module.SERVICES['user']}/users"]


def test_post_user_is_forwarded_with_body_and_status(gateway_client, gateway_module, monkeypatch, fake_response):
    sent = {}

    def fake_post(url, json=None, **kw):
        sent["url"], sent["json"] = url, json
        return fake_response({"id": 5, **json}, 201)

    monkeypatch.setattr(requests, "post", fake_post)
    r = gateway_client.post("/api/users", json={"name": "Asha", "email": "asha@example.com"})
    assert r.status_code == 201
    assert r.get_json()["id"] == 5
    assert sent["url"] == f"{gateway_module.SERVICES['user']}/users"
    assert sent["json"] == {"name": "Asha", "email": "asha@example.com"}


def test_get_products_is_forwarded(gateway_client, gateway_module, monkeypatch, fake_response):
    calls = []
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: calls.append(url) or fake_response([{"id": 101}], 200),
    )
    r = gateway_client.get("/api/products")
    assert r.status_code == 200
    assert calls == [f"{gateway_module.SERVICES['product']}/products"]


def test_get_orders_is_forwarded(gateway_client, gateway_module, monkeypatch, fake_response):
    calls = []
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: calls.append(url) or fake_response([], 200),
    )
    r = gateway_client.get("/api/orders")
    assert r.status_code == 200
    assert calls == [f"{gateway_module.SERVICES['order']}/orders"]


def test_post_order_passes_through_backend_status(gateway_client, gateway_module, monkeypatch, fake_response):
    monkeypatch.setattr(
        requests, "post",
        lambda url, json=None, **kw: fake_response({"error": "Not enough stock"}, 400),
    )
    r = gateway_client.post("/api/orders", json={"user_id": 1, "product_id": 101, "qty": 999})
    assert r.status_code == 400
    assert r.get_json()["error"] == "Not enough stock"


@pytest.mark.parametrize("path", ["/api/products", "/gateway/status"])
def test_write_methods_not_allowed_on_read_only_routes(gateway_client, path):
    assert gateway_client.post(path, json={}).status_code == 405


def test_unknown_route_returns_404(gateway_client):
    assert gateway_client.get("/api/does-not-exist").status_code == 404
