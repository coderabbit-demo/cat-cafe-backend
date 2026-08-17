from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth
from app.main import app
from app.services.store import SessionRecord, store


@pytest.fixture(autouse=True)
def reset_store() -> Iterator[None]:
    store.users.clear()
    store.user_emails.clear()
    store.google_identities.clear()
    store.sessions.clear()
    store.reservations.clear()
    yield


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        auth,
        "verify_google_id_token",
        lambda credential: {
            "sub": credential,
            "email": f"{credential}@example.com",
            "email_verified": True,
        },
    )
    return TestClient(app)


def sign_in(client: TestClient, subject: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/google", json={"credential": subject})
    assert response.status_code == 200
    return response.json()


def test_google_sign_in_sets_session_and_supports_logout(client: TestClient) -> None:
    user = sign_in(client, "google-user")
    response = client.post("/api/v1/auth/google", json={"credential": "google-user"})

    assert client.cookies.get("cat_cafe_session")
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert client.get("/api/v1/auth/me").json() == user
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_session_is_rejected(client: TestClient) -> None:
    sign_in(client, "google-user")
    token = client.cookies.get("cat_cafe_session")
    assert token
    session = store.sessions[token]
    store.sessions[token] = SessionRecord(
        user_id=session.user_id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    assert client.get("/api/v1/auth/me").status_code == 401
    assert token not in store.sessions


def test_creating_session_evicts_abandoned_expired_sessions(client: TestClient) -> None:
    user = sign_in(client, "google-user")
    abandoned_token = client.cookies.get("cat_cafe_session")
    assert abandoned_token
    store.sessions[abandoned_token] = SessionRecord(
        user_id=store.sessions[abandoned_token].user_id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    store.create_session(user_id=UUID(user["id"]), ttl_seconds=60)

    assert abandoned_token not in store.sessions


def test_session_store_has_a_hard_size_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = sign_in(client, "google-user")
    first_token = client.cookies.get("cat_cafe_session")
    assert first_token
    monkeypatch.setattr(store, "MAX_SESSIONS", 2)

    store.create_session(user_id=UUID(user["id"]), ttl_seconds=60)
    store.create_session(user_id=UUID(user["id"]), ttl_seconds=60)

    assert len(store.sessions) == 2
    assert first_token not in store.sessions


def test_invalid_google_credential_is_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(_credential: str) -> dict[str, str]:
        raise ValueError("bad token")

    monkeypatch.setattr(auth, "verify_google_id_token", reject)
    response = client.post("/api/v1/auth/google", json={"credential": "invalid"})
    assert response.status_code == 401


def test_reservations_require_authentication() -> None:
    anonymous_client = TestClient(app)
    assert anonymous_client.get("/api/v1/reservations").status_code == 401
    assert anonymous_client.post("/api/v1/reservations", json={}).status_code == 401


def test_reservations_are_scoped_to_the_current_user(client: TestClient) -> None:
    first_user = sign_in(client, "first")
    created = client.post(
        "/api/v1/reservations",
        json={
            "reservation_date": "2026-08-18",
            "start_time": "10:00",
            "guest_count": 2,
        },
    )
    assert created.status_code == 201
    reservation = created.json()
    assert reservation["user_id"] == first_user["id"]

    other_client = TestClient(app)
    sign_in(other_client, "second")
    assert other_client.get("/api/v1/reservations").json() == []
    assert other_client.delete(f"/api/v1/reservations/{reservation['id']}").status_code == 404
    assert client.delete(f"/api/v1/reservations/{reservation['id']}").status_code == 204
