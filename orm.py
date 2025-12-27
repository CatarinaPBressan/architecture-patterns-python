from sqlalchemy import Column, Table
from sqlalchemy.orm import registry
from sqlalchemy.types import Date, Integer, String

import models

mapper_registry = registry()

order_lines = Table(
    "order_lines",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False),
    Column("order_id", String(255)),
)

batches = Table(
    "batches",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("eta", Date, nullable=True),
    Column("purchased_quantity", Integer),
)


def start_mappers():
    mapper_registry.map_imperatively(models.OrderLine, order_lines)
    mapper_registry.map_imperatively(models.Batch, batches)
