"""
Shared test setup.

The services keep their data in plain Python dictionaries (in memory).
Tests that change data (create a user, reduce stock, place an order) would
leak into the next test, so the fixtures below restore the original data
after every test.
"""
import copy
import os
import sys

import pytest

# Make "import product_service" etc. work when pytest runs from any folder.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ---------- a tiny fake for requests.Response ----------
class FakeResponse:
    """Stands in for the HTTP response of another microservice."""

    def __init__(self, json_data=None, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json


@pytest.fixture
def fake_response():
    return FakeResponse


# ---------- product service ----------
@pytest.fixture
def product_module():
    import product_service

    original = copy.deepcopy(product_service.PRODUCTS)
    yield product_service
    product_service.PRODUCTS.clear()
    product_service.PRODUCTS.update(original)


@pytest.fixture
def product_client(product_module):
    return product_module.app.test_client()


# ---------- user service ----------
@pytest.fixture
def user_module():
    import user_service

    original = copy.deepcopy(user_service.USERS)
    yield user_service
    user_service.USERS.clear()
    user_service.USERS.update(original)


@pytest.fixture
def user_client(user_module):
    return user_module.app.test_client()


# ---------- order service ----------
@pytest.fixture
def order_module():
    import order_service

    order_service.ORDERS.clear()
    order_service.next_order_id = 1
    yield order_service
    order_service.ORDERS.clear()
    order_service.next_order_id = 1


@pytest.fixture
def order_client(order_module):
    return order_module.app.test_client()


# ---------- api gateway ----------
@pytest.fixture
def gateway_module():
    import api_gateway

    return api_gateway


@pytest.fixture
def gateway_client(gateway_module):
    return gateway_module.app.test_client()
