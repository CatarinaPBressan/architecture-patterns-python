from sqlalchemy import select, text
from sqlalchemy.orm import Session

import models
from orm import order_lines


def test_orderline_mapper_can_load_lines(session: Session):
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


def test_orderline_mapper_can_load_lines_select_by_table(session: Session):
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

    assert session.execute(select(order_lines)).all() == expected


def test_orderline_mapper_can_save_lines(session: Session):
    new_line = models.OrderLine("order_1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()

    rows = list(
        session.execute(text('SELECT order_id, sku, quantity from "order_lines"'))
    )
    assert rows == [("order_1", "DECORATIVE-WIDGET", 12)]
