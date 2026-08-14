"""
Tests de autenticación para DevCommunity API.

Verifica:
- Login correcto (JSON + form-data)
- Login incorrecto (credenciales inválidas)
- Endpoint sin token → 401
- Endpoint con token inválido → 401
- Endpoint autenticado correctamente
- /auth/me retorna datos del usuario
- /openapi.json muestra un solo esquema de seguridad OAuth2
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.auth.auth_routes import hash_password

# ---------- Test DB setup ----------

SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Mock Redis para evitar dependencia de Redis real en tests
@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis client globally so tests don't require a running Redis server."""
    fake_redis = MagicMock()
    fake_redis.exists.return_value = False  # token not blacklisted
    fake_redis.get.return_value = None
    fake_redis.setex.return_value = True
    fake_redis.delete.return_value = True

    with patch("app.auth.auth_handler.redis_client", fake_redis), \
         patch("app.auth.auth_routes.redis_client", fake_redis), \
         patch("app.auth.auth_routes.session_service") as mock_session_svc:
        mock_session_svc.create_session.return_value = {}
        mock_session_svc.get_sessions.return_value = []
        mock_session_svc.get_metrics_for_user.return_value = {}
        yield fake_redis


@pytest.fixture(autouse=True)
def setup_db():
    """Crea las tablas antes de cada test y las elimina después."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user():
    """Inserta un usuario de prueba en la BD y devuelve sus datos."""
    db = TestSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password123"),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"id": user.id, "email": "test@example.com", "password": "password123", "username": "testuser"}


def _login(client: TestClient, email: str, password: str) -> dict:
    """Helper: login via JSON y devuelve el body de respuesta."""
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp


# =====================================================================
# Login correcto
# =====================================================================


class TestLoginCorrect:
    def test_login_json_returns_tokens(self, client, test_user):
        resp = _login(client, test_user["email"], test_user["password"])
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_form_data_returns_tokens(self, client, test_user):
        """Verifica que /auth/token (form-data para Swagger) funcione."""
        resp = client.post(
            "/auth/token",
            data={"username": test_user["email"], "password": test_user["password"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"


# =====================================================================
# Login incorrecto
# =====================================================================


class TestLoginIncorrect:
    def test_wrong_password(self, client, test_user):
        resp = _login(client, test_user["email"], "wrongpassword123")
        assert resp.status_code == 401

    def test_nonexistent_user(self, client):
        resp = _login(client, "nobody@example.com", "password123")
        assert resp.status_code == 401

    def test_form_data_wrong_password(self, client, test_user):
        resp = client.post(
            "/auth/token",
            data={"username": test_user["email"], "password": "wrongpassword123"},
        )
        assert resp.status_code == 401


# =====================================================================
# Endpoints sin token → 401
# =====================================================================


class TestNoToken:
    @pytest.mark.parametrize("method,path", [
        ("GET", "/auth/me"),
        ("GET", "/auth/sessions"),
        ("GET", "/auth/sessions/metrics"),
        ("GET", "/posts/"),
    ])
    def test_protected_endpoint_without_token(self, client, method, path):
        resp = client.request(method, path)
        assert resp.status_code == 401


# =====================================================================
# Endpoints con token inválido → 401
# =====================================================================


class TestInvalidToken:
    @pytest.mark.parametrize("path", [
        "/auth/me",
        "/posts/",
    ])
    def test_invalid_token(self, client, path):
        resp = client.get(path, headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


# =====================================================================
# Endpoint autenticado correctamente
# =====================================================================


class TestAuthenticated:
    def test_me_returns_user_data(self, client, test_user):
        login_resp = _login(client, test_user["email"], test_user["password"])
        token = login_resp.json()["access_token"]

        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == test_user["email"]
        assert body["username"] == test_user["username"]
        assert body["id"] == test_user["id"]

    def test_authenticated_endpoint_works(self, client, test_user):
        login_resp = _login(client, test_user["email"], test_user["password"])
        token = login_resp.json()["access_token"]

        resp = client.get("/posts/", headers={"Authorization": f"Bearer {token}"})
        # Should not be 401 (auth succeeded)
        assert resp.status_code != 401


# =====================================================================
# OpenAPI schema — un solo esquema de seguridad
# =====================================================================


class TestOpenAPI:
    def test_single_security_scheme(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()

        security_schemes = schema.get("components", {}).get("securitySchemes", {})
        # Debe existir exactamente un esquema de seguridad (OAuth2PasswordBearer)
        assert len(security_schemes) == 1, (
            f"Se esperaba 1 esquema de seguridad, se encontraron {len(security_schemes)}: "
            f"{list(security_schemes.keys())}"
        )

        scheme_name = list(security_schemes.keys())[0]
        scheme = security_schemes[scheme_name]
        assert scheme["type"] == "oauth2"
        assert "password" in scheme["flows"]
        assert scheme["flows"]["password"]["tokenUrl"] == "/auth/token"
