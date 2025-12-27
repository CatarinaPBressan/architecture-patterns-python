from sqlalchemy import Column, MetaData, Table
from sqlalchemy.orm import Mapper
from sqlalchemy.types import Date, Integer, String

import models

metadata = MetaData()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False),
    Column("order_id", String(255)),
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("eta", Date, nullable=True),
    Column("purchased_quantity", Integer),
)


def start_mappers():
    order_lines_mapper = Mapper(models.OrderLine, order_lines)
    batches_mapper = Mapper(models.Batch, batches)

    return (order_lines_mapper, batches_mapper)
