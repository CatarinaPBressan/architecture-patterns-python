import sqlalchemy
from sqlalchemy import orm, schema, types

from allocations.domain import models

mapper_registry = orm.registry()

order_lines = schema.Table(
    "order_lines",
    mapper_registry.metadata,
    sqlalchemy.Column("id", types.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("sku", types.String(255)),
    sqlalchemy.Column("quantity", types.Integer, nullable=False),
    sqlalchemy.Column("order_id", types.String(255)),
    sqlalchemy.Column("batch_id", types.Integer, schema.ForeignKey("batches.id")),
)

batches = schema.Table(
    "batches",
    mapper_registry.metadata,
    sqlalchemy.Column("id", types.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("reference", types.String(255)),
    sqlalchemy.Column("sku", types.String(255)),
    sqlalchemy.Column("eta", types.Date, nullable=True),
    sqlalchemy.Column("_purchased_quantity", types.Integer),
)


def start_mappers():
    mapper_registry.map_imperatively(models.OrderLine, order_lines)
    mapper_registry.map_imperatively(
        models.Batch,
        batches,
        properties={
            "_allocations": orm.relationship(models.OrderLine, collection_class=set)
        },
    )
