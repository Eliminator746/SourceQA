from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from app.rag.ingestion import ingest_documents
from app.rag.loaders import load_document
from types import SimpleNamespace
from app.models.user import User as UserModel
import app.core.database as _app_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, SessionLocal as AppSessionLocal, engine as AppEngine
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



@pytest.fixture(scope="session", autouse=True)
def use_test_database(tmp_path_factory):
    """Set up a temporary SQLite database for the whole test session and
    patch the application's SessionLocal and engine to use it.
    """

    db_dir = tmp_path_factory.mktemp("data")
    db_file = db_dir / "test_db.sqlite"
    url = f"sqlite:///{db_file}"

    test_engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    # create tables
    Base.metadata.create_all(test_engine)

    import app.core.database as _db

    # patch
    original_engine = _db.engine
    original_sessionlocal = _db.SessionLocal
    _db.engine = test_engine
    _db.SessionLocal = TestSessionLocal

    yield

    # teardown
    Base.metadata.drop_all(test_engine)
    _db.engine = original_engine
    _db.SessionLocal = original_sessionlocal


@pytest.fixture
def client():

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(client):

    email = f"test_{uuid.uuid4()}@example.com"
    password = "TestPassword123!"

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 201

    # attempt to load the created user from the (possibly patched) SessionLocal
    db = _app_db.SessionLocal()
    user = db.query(UserModel).filter(UserModel.email == email).first()
    db.close()

    # Wrap the SQLAlchemy user so tests can use attribute access and
    # item access (e.g., test_user['email']). Also expose `password`
    # so tests can log in.
    class TestUser:
        def __init__(self, model, password):
            self._model = model
            self.password = password

        @property
        def id(self):
            return self._model.id

        @property
        def email(self):
            return self._model.email

        @property
        def created_at(self):
            return getattr(self._model, "created_at", None)

        def __getitem__(self, key):
            return getattr(self, key)

    return TestUser(user, password)


@pytest.fixture
def auth_headers(client, test_user):

    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def override_user(test_user):

    app.dependency_overrides[
        get_current_user
    ] = lambda: test_user

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def indexed_documents():
    # Create a small set of in-memory documents for tests to avoid
    # calling external embedding APIs or loading files.
    class SimpleDoc:
        def __init__(self, text, metadata=None):
            self.page_content = text
            self.metadata = metadata or {}
            # BM25 retriever expects an `id` attribute
            from uuid import uuid4

            self.id = str(uuid4())

    docs = [
        SimpleDoc(
            "Tesla experienced strong stock-price growth despite declining fundamentals.",
            {"filename": "report.pdf", "user_id": "test-user-001"}
        ),
        SimpleDoc(
            "Another company showed moderate growth.",
            {"filename": "report.pdf", "user_id": "test-user-001"}
        ),
    ]

    return docs


@pytest.fixture
def db_session(tmp_path):
    """Create a temporary SQLite database and patch the application's
    SessionLocal/engine to use it so integration tests can run against
    an isolated database.
    """

    # create sqlite file
    db_file = tmp_path / "test_db.sqlite"
    url = f"sqlite:///{db_file}"

    test_engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    # create tables
    Base.metadata.create_all(test_engine)

    # patch the app's SessionLocal and engine so get_db yields sessions from
    # the test database
    import app.core.database as _db

    _db.engine = test_engine
    _db.SessionLocal = TestSessionLocal

    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(test_engine)
        # restore original engine/session if needed
        _db.engine = AppEngine
        _db.SessionLocal = AppSessionLocal