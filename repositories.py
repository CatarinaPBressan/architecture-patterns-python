import abc

from sqlalchemy import orm, select

import models
import orm as allocations_orm


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: models.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: str) -> models.Batch:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[models.Batch]:
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):

    session: orm.Session

    def __init__(self, session: orm.Session):
        self.session = session

    def add(self, batch: models.Batch):
        self.session.add(batch)

    def get(self, reference: str) -> models.Batch | None:
        return self.session.scalar(
            select(models.Batch).where(allocations_orm.batches.c.reference == reference)
        )

    def list(self) -> list[models.Batch]:
        return list(self.session.scalars(select(models.Batch)).all())


class FakeRepository(AbstractRepository):

    _batches: set[models.Batch]

    def __init__(self, batches) -> None:
        self._batches = set(batches)

    def add(self, batch: models.Batch):
        self._batches.add(batch)

    def get(self, reference: str) -> models.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list[models.Batch]:
        return list(self._batches)
