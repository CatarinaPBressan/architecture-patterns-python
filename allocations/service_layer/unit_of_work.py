import abc
import datetime

from sqlalchemy import orm as sqlalchemy_orm

from allocations.adapters import repositories
from allocations.domain import models


class AbstractUnitOfWork(abc.ABC):
    batches: repositories.AbstractRepository

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, tb):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):

    session: sqlalchemy_orm.Session
    session_factory: sqlalchemy_orm.sessionmaker

    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = repositories.SQLAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, exc_type, exc, tb):
        super().__exit__(exc_type, exc, tb)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.batches = repositories.FakeRepository([])
        self.commited = False

    def commit(self):
        self.commited = True

    def rollback(self):
        pass

    @staticmethod
    def for_batch(
        reference: str, sku: str, quantity: int, eta: datetime.date | None
    ) -> "FakeUnitOfWork":
        uow = FakeUnitOfWork()
        uow.batches.add(models.Batch(reference, sku, quantity, eta))
        return uow
