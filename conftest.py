import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import config
import flask_app
import orm as allocations_orm


@pytest.fixture
def session():
    engine = sqlalchemy.create_engine(config.get_memory_sqlite(), echo=True)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()
    _session = sessionmaker(bind=engine)()

    yield _session

    allocations_orm.mapper_registry.metadata.drop_all(engine)
    allocations_orm.mapper_registry.dispose()


@pytest.fixture
def flask_test_client(session):
    app = flask_app.init_app()
    return app.test_client()
