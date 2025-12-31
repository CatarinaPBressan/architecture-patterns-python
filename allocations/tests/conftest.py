import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import from  config
import flask_app
import orm as allocations_orm


@pytest.fixture
def make_session():
    engine = sqlalchemy.create_engine(config.get_sqlite(), echo=True)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()

    yield sessionmaker(bind=engine)

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
