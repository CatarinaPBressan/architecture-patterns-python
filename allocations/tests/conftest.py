import pytest
import sqlalchemy
import sqlalchemy.orm as sqlalchemy_orm

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.entrypoints import flask_app


@pytest.fixture
def make_session():
    engine = sqlalchemy.create_engine(config.get_sqlite(), echo=True)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()

    yield sqlalchemy_orm.sessionmaker(bind=engine)

    allocations_orm.mapper_registry.metadata.drop_all(engine)
    allocations_orm.mapper_registry.dispose()


@pytest.fixture
def session(make_session):
    _session = make_session()

    yield _session


@pytest.fixture
def flask_test_client(make_session):
    app = flask_app.init_app(make_session)
    return app.test_client()
