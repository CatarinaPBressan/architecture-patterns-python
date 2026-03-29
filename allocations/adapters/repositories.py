import abc
import datetime

from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import select

from allocations.adapters import orm as allocations_orm
from allocations.domain import models


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: models.Batch) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: str) -> models.Batch | None:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[models.Batch]:
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):

    session: sqlalchemy_orm.Session

    def __init__(self, session: sqlalchemy_orm.Session):
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

    def __init__(self, batches: list[models.Batch]) -> None:
        self._batches = set(batches)

    def add(self, batch: models.Batch):
        self._batches.add(batch)

    def get(self, reference: str) -> models.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list[models.Batch]:
        return list(self._batches)

    @staticmethod
    def for_batch(reference: str, sku: str, quantity: int, eta: datetime.date | None):
        return FakeRepository([models.Batch(reference, sku, quantity, eta)])


class AbstractProductRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: models.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku: str) -> models.Product | None:
        raise NotImplementedError


class SQLAlchemyProductRepository(AbstractProductRepository):
    session: sqlalchemy_orm.Session

    def __init__(self, session: sqlalchemy_orm.Session) -> None:
        self.session = session

    def get(self, sku: str) -> models.Product | None:
        return self.session.scalar(
            select(models.Product).where(allocations_orm.products.c.sku == sku)
        )

    def add(self, product: models.Product) -> None:
        self.session.add(product)
