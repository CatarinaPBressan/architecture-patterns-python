import abc
import datetime
import sqlite3

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
        return self.session.scalars(select(models.Batch)).all()


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


class RawSQLRepository(AbstractRepository):

    _connection: sqlite3.Connection

    def __init__(self) -> None:
        self._connection = sqlite3.connect(":memory:")
        self._init_tables()

    def __del__(self):
        self._connection.close()
        pass

    def _init_tables(self):
        cursor = self._connection.cursor()
        cursor.execute(
            "CREATE TABLE order_lines ("
            "id INTEGER PRIMARY KEY, "
            "sku TEXT, "
            "quantity INTEGER, "
            "order_id TEXT, "
            "batch_id INTEGER "
            ")"
        )
        cursor.execute(
            "CREATE TABLE batches ("
            "id INTEGER PRIMARY KEY, "
            "reference TEXT, "
            "sku TEXT, "
            "eta TEXT, "
            "purchased_quantity INTEGER "
            ")"
        )

    def _to_model(self, row: tuple[str, str, int, str]) -> models.Batch:
        return models.Batch(row[0], row[1], row[2], datetime.date.fromisoformat(row[3]))

    def commit(self):
        self._connection.commit()

    def add(self, batch: models.Batch):
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO batches "
            "(reference, sku, eta, purchased_quantity)"
            "VALUES (?, ?, ?, ?)",
            (
                batch.reference,
                batch.sku,
                batch.eta.isoformat(),
                batch._purchased_quantity,
            ),
        )

    def get(self, reference: str) -> models.Batch:
        cursor = self._connection.cursor()
        row = cursor.execute(
            "SELECT reference, sku, purchased_quantity, eta "
            "FROM batches "
            "WHERE reference = ?",
            (reference,),
        ).fetchone()

        return self._to_model(row)

    def list(self) -> list[models.Batch]:
        cursor = self._connection.cursor()
        return [
            self._to_model(row)
            for row in cursor.execute(
                "SELECT reference, sku, purchased_quantity, eta FROM batches"
            )
        ]
