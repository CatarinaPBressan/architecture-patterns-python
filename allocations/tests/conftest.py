import uuid
from typing import Generator

import dotenv
import pytest
import sqlalchemy
import sqlalchemy.orm as sqlalchemy_orm
from fastapi.testclient import TestClient

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.entrypoints import flask_app


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()


@pytest.fixture
def make_session():
    engine = sqlalchemy.create_engine(
        config.get_postgres(test=True), echo=True, **config.get_postgres_engine_kwargs()
    )
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()

    yield sqlalchemy_orm.sessionmaker(bind=engine)

    allocations_orm.mapper_registry.metadata.drop_all(engine)
    allocations_orm.mapper_registry.dispose()


@pytest.fixture
def session(make_session):
    _session = make_session()

    yield _session

    # close out sessions, otherwise postgres will hold very aggressive locks
    # even on SELECTS
    _session.rollback()


@pytest.fixture
def flask_test_client(make_session):
    app = flask_app.init_app(make_session)
    return app.test_client()


@pytest.fixture
def fastapi_test_client(make_session):
    def test_db_override() -> Generator[sqlalchemy_orm.Session, None, None]:
        return make_session

    from allocations.entrypoints.fastapi_app import app, session_maker

    app.dependency_overrides[session_maker] = test_db_override

    yield TestClient(app)

    app.dependency_overrides = {}


@pytest.fixture
def random_uuid_hex():
    return lambda: uuid.uuid4().hex.upper()


@pytest.fixture
def random_sku(random_uuid_hex):
    return lambda: f"SKU {random_uuid_hex()}"


@pytest.fixture
def random_batch_ref(random_uuid_hex):
    return lambda: f"BATCH {random_uuid_hex()}"


@pytest.fixture
def random_order_id(random_uuid_hex):
    return lambda: f"ORDER {random_uuid_hex()}"
