"""Unit tests for USER SERVICE (port 5002)."""
import pytest


def test_health_is_up(user_client):
    r = user_client.get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["service"] == "user-service"
    assert body["status"] == "UP"


def test_list_users(user_client):
    r = user_client.get("/users")
    assert r.status_code == 200
    users = r.get_json()
    assert len(users) >= 1
    for u in users:
        assert {"id", "name", "email"} <= set(u)


def test_get_single_user(user_client):
    r = user_client.get("/users/1")
    assert r.status_code == 200
    assert r.get_json()["id"] == 1


def test_get_unknown_user_returns_404(user_client):
    r = user_client.get("/users/99999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "User not found"


def test_create_user_returns_201_and_new_id(user_client, user_module):
    expected_id = max(user_module.USERS) + 1
    r = user_client.post("/users", json={"name": "Test Student", "email": "student@example.com"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["id"] == expected_id
    assert body["name"] == "Test Student"
    assert body["email"] == "student@example.com"


def test_created_user_can_be_fetched_again(user_client):
    created = user_client.post("/users", json={"name": "Ravi", "email": "ravi@example.com"}).get_json()
    r = user_client.get(f"/users/{created['id']}")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Ravi"


def test_create_user_increases_user_count(user_client):
    before = len(user_client.get("/users").get_json())
    user_client.post("/users", json={"name": "A", "email": "a@example.com"})
    after = len(user_client.get("/users").get_json())
    assert after == before + 1


@pytest.mark.xfail(
    reason="KNOWN ISSUE: a POST with no JSON body crashes with 500 instead of 400",
    strict=False,
)
def test_create_user_without_json_body_is_a_client_error(user_client):
    r = user_client.post("/users")
    assert r.status_code == 400
