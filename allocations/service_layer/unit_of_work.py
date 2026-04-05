import abc

from sqlalchemy import orm as sqlalchemy_orm

from allocations.adapters import repositories


class AbstractProductUnitOfWork(abc.ABC):
    products: repositories.AbstractProductRepository

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class SQLAlchemyProductUnitOfWork(AbstractProductUnitOfWork):
    session: sqlalchemy_orm.Session
    session_factory: sqlalchemy_orm.sessionmaker

    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory(expire_on_commit=False)
        self.products = repositories.SQLAlchemyProductRepository(self.session)
        return super().__enter__()

    def __exit__(self, exc_type, exc, tb):
        super().__exit__(exc_type, exc, tb)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
