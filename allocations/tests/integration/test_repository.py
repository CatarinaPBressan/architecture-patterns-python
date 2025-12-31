from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import text

from allocations.adapters import repositories
from allocations.domain import models


def insert_order_line(order_id: str, sku: str, session: sqlalchemy_orm.Session) -> int:
    params = {"order_id": order_id, "sku": sku}

    session.execute(
        text(
            "INSERT INTO order_lines (order_id, sku, quantity)"
            "VALUES (:order_id, :sku, 1)"
        ),
        params,
    )

    order_line_id: int = session.scalar(
        text("SELECT id FROM order_lines WHERE order_id= :order_id AND sku= :sku"),
        params,
    )

    return order_line_id


def insert_batch(reference: str, sku: str, session: sqlalchemy_orm.Session) -> int:
    params = {"reference": reference, "sku": sku}
    session.execute(
        text(
            "INSERT INTO batches (reference, sku, eta, _purchased_quantity)"
            "VALUES (:reference, :sku, NULL, 10)"
        ),
        params,
    )

    batch_id: int = session.scalar(
        text("SELECT id FROM batches WHERE reference= :reference AND sku= :sku"), params
    )
    return batch_id


def insert_allocation(
    order_line_id: int, batch_id: int, session: sqlalchemy_orm.Session
):
    params = {"order_line_id": order_line_id, "batch_id": batch_id}

    session.execute(
        text("UPDATE order_lines SET batch_id= :batch_id WHERE id= :order_line_id"),
        params,
    )


def test_repository_can_retrieve_a_batch_with_allocations(
    session: sqlalchemy_orm.Session,
):
    sku = "GENERIC-SOFA"
    reference = "batchref"
    order_line_id = insert_order_line("order123", sku, session)
    batch_id = insert_batch(reference, sku, session)
    insert_allocation(order_line_id, batch_id, session)
    repo = repositories.SQLAlchemyRepository(session)

    retrieved = repo.get(reference)

    expected = models.Batch(reference, sku, 10)
    assert retrieved
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {models.OrderLine("order123", sku, 1)}


def test_repository_can_save_a_batch(session: sqlalchemy_orm.Session):
    batch = models.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
    repo = repositories.SQLAlchemyRepository(session)

    repo.add(batch)
    session.commit()

    rows = list(
        session.execute(
            text('SELECT reference, sku, _purchased_quantity, eta FROM "batches"')
        )
    )

    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]
