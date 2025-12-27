import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import orm as allocations_orm


@pytest.fixture
def session():
    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:", echo=True)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()
    _session = sessionmaker(bind=engine)()

    yield _session

    allocations_orm.mapper_registry.metadata.drop_all(engine)
    allocations_orm.mapper_registry.dispose()
