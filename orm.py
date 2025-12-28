import datetime

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    registry,
    relationship,
)
from sqlalchemy.types import Date, Integer, String

import models

mapper_registry = registry()


# class Base(DeclarativeBase):
#     pass


@mapper_registry.mapped
class OrderLines:
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str]
    quantity: Mapped[int] = mapped_column(nullable=False)
    order_id: Mapped[str | None]
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"))


@mapper_registry.mapped
class Batches:
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reference: Mapped[str]
    sku: Mapped[str]
    eta: Mapped[datetime.date | None]
    _purchased_quantity: Mapped[int]
    _allocations: Mapped[set[models.Batch]] = relationship(
        models.OrderLine, collection_class=set
    )


# order_lines = Table(
#     "order_lines",
#     mapper_registry.metadata,
#     Column("id", Integer, primary_key=True, autoincrement=True),
#     Column("sku", String(255)),
#     Column("quantity", Integer, nullable=False),
#     Column("order_id", String(255)),
#     Column("batch_id", Integer, ForeignKey("batches.id")),
# )

# batches = Table(
#     "batches",
#     mapper_registry.metadata,
#     Column("id", Integer, primary_key=True, autoincrement=True),
#     Column("reference", String(255)),
#     Column("sku", String(255)),
#     Column("eta", Date, nullable=True),
#     Column("_purchased_quantity", Integer),
# )


def start_mappers():
    pass
    mapper_registry.map_imperatively(models.OrderLine, OrderLines)
    mapper_registry.map_imperatively(models.Batch, Batches)


#     mapper_registry.map_imperatively(models.OrderLine, order_lines)
#     mapper_registry.map_imperatively(
#         models.Batch,
#         batches,
#         properties={
#             "_allocations": relationship(models.OrderLine, collection_class=set)
#         },
#     )
