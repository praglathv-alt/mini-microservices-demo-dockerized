"""Unit tests for PRODUCT SERVICE (port 5001)."""
import pytest


def test_health_is_up(product_client):
    r = product_client.get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["service"] == "product-service"
    assert body["status"] == "UP"


def test_list_products_returns_catalog(product_client):
    r = product_client.get("/products")
    assert r.status_code == 200
    products = r.get_json()
    assert len(products) >= 1
    for p in products:
        assert {"id", "name", "price", "stock"} <= set(p)
        assert p["price"] > 0
        assert p["stock"] >= 0


def test_get_single_product(product_client):
    r = product_client.get("/products/101")
    assert r.status_code == 200
    assert r.get_json()["id"] == 101


def test_get_unknown_product_returns_404(product_client):
    r = product_client.get("/products/99999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "Product not found"


def test_reduce_stock_decreases_stock(product_client, product_module):
    before = product_module.PRODUCTS[101]["stock"]
    r = product_client.post("/products/101/reduce_stock", json={"qty": 3})
    assert r.status_code == 200
    assert r.get_json()["stock"] == before - 3
    assert product_module.PRODUCTS[101]["stock"] == before - 3


def test_reduce_stock_defaults_to_one(product_client, product_module):
    before = product_module.PRODUCTS[101]["stock"]
    r = product_client.post("/products/101/reduce_stock", json={})
    assert r.status_code == 200
    assert product_module.PRODUCTS[101]["stock"] == before - 1


def test_reduce_stock_insufficient_stock_is_rejected(product_client, product_module):
    before = product_module.PRODUCTS[101]["stock"]
    r = product_client.post("/products/101/reduce_stock", json={"qty": before + 1})
    assert r.status_code == 400
    assert r.get_json()["error"] == "Insufficient stock"
    # stock must not change when the request is rejected
    assert product_module.PRODUCTS[101]["stock"] == before


def test_reduce_stock_unknown_product_returns_404(product_client):
    r = product_client.post("/products/99999/reduce_stock", json={"qty": 1})
    assert r.status_code == 404


@pytest.mark.xfail(
    reason="KNOWN ISSUE: a POST with no JSON body crashes with 500 instead of 400",
    strict=False,
)
def test_reduce_stock_without_json_body_is_a_client_error(product_client):
    r = product_client.post("/products/101/reduce_stock")
    assert r.status_code == 400
