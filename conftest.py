import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import orm as allocations_orm


@pytest.fixture
def session():
    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:")
    # metadata = allocations_orm.Base.metadata
    metadata = allocations_orm.mapper_registry.metadata

    metadata.create_all(engine)
    allocations_orm.start_mappers()
    _session = sessionmaker(bind=engine)()

    yield _session

    metadata.drop_all(engine)
