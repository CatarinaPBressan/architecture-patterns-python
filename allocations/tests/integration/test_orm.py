from sqlalchemy import create_engine
from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.domain import models


def test_orderline_mapper_can_load_lines(session: sqlalchemy_orm.Session):
    session.execute(
        text(
            "INSERT INTO order_lines (order_id, sku, quantity) VALUES"
            ' ("order1", "RED-CHAIR", 12),'
            ' ("order1", "BLUE-TABLE", 13),'
            ' ("order1", "BLUE-LIPSTICK", 14)'
        )
    )

    expected = [
        models.OrderLine("order1", "RED-CHAIR", 12),
        models.OrderLine("order1", "BLUE-TABLE", 13),
        models.OrderLine("order1", "BLUE-LIPSTICK", 14),
    ]

    assert session.scalars(select(models.OrderLine)).all() == expected


def test_orderline_mapper_can_load_lines_select_by_table(
    session: sqlalchemy_orm.Session,
):
    session.execute(
        text(
            "INSERT INTO order_lines (order_id, sku, quantity) VALUES"
            ' ("order1", "RED-CHAIR", 12),'
            ' ("order1", "BLUE-TABLE", 13),'
            ' ("order1", "BLUE-LIPSTICK", 14)'
        )
    )

    expected = [
        (1, "RED-CHAIR", 12, "order1", None),
        (2, "BLUE-TABLE", 13, "order1", None),
        (3, "BLUE-LIPSTICK", 14, "order1", None),
    ]

    assert session.execute(select(allocations_orm.order_lines)).all() == expected


def test_orderline_mapper_can_save_lines(postgres_session: sqlalchemy_orm.Session):
    new_line = models.OrderLine("order_1", "DECORATIVE-WIDGET", 12)

    postgres_session.add(new_line)
    postgres_session.commit()

    rows = list(postgres_session.execute(select(models.OrderLine)).all())
    assert rows == [models.OrderLine("order_1", "DECORATIVE-WIDGET", 12)]


async def test_async_postgres():
    engine = create_async_engine(config.get_postgres())
    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT 1")) == 1


def test_postgres():
    engine = create_engine(config.get_postgres())
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
