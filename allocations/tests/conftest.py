import uuid

import dotenv
import pytest
import sqlalchemy
import sqlalchemy.orm as sqlalchemy_orm

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.entrypoints import flask_app


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()


@pytest.fixture
def make_session():
    engine = sqlalchemy.create_engine(config.get_postgres(test=True), echo=True)
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


def _random_uuid4():
    return str(uuid.uuid4())[:8]


@pytest.fixture
def random_sku():
    return lambda: f"SKU {_random_uuid4()}"


@pytest.fixture
def random_batch_ref():
    return lambda: f"BATCH {_random_uuid4()}"


@pytest.fixture
def random_order_id():
    return lambda: f"ORDER {_random_uuid4()}"
