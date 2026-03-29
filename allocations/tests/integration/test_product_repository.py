from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import text

from allocations.adapters import repositories
from allocations.domain import models


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


def insert_allocation(order_line_id: int, batch_id: int, session: sqlalchemy_orm.Session):
    params = {"order_line_id": order_line_id, "batch_id": batch_id}

    session.execute(
        text("UPDATE order_lines SET batch_id= :batch_id WHERE id= :order_line_id"),
        params,
    )


def insert_order_line(order_id: str, sku: str, session: sqlalchemy_orm.Session) -> int:
    params = {"order_id": order_id, "sku": sku}

    session.execute(
        text("INSERT INTO order_lines (order_id, sku, quantity) VALUES (:order_id, :sku, 1)"),
        params,
    )

    order_line_id: int = session.scalar(
        text("SELECT id FROM order_lines WHERE order_id= :order_id AND sku= :sku"),
        params,
    )

    return order_line_id


def insert_product(sku: str, session: sqlalchemy_orm.Session) -> int:
    params = {"sku": sku}

    session.execute(text("INSERT INTO products (sku) VALUES (:sku)"), params)

    product_id: int = session.scalar(text("SELECT id FROM products WHERE sku= :sku"), params)
    return product_id


def test_get_product_with_batches_and_allocations(
    session, random_batch_ref, random_sku, random_order_id
):
    sku = random_sku()
    batch_reference = random_batch_ref()
    order_id = random_order_id()
    order_line_id = insert_order_line(order_id, sku, session)
    batch_id = insert_batch(batch_reference, sku, session)
    insert_allocation(order_line_id, batch_id, session)
    insert_product(sku, session)
    product_repository = repositories.SQLAlchemyProductRepository(session)

    product = product_repository.get(sku)

    assert product
    assert len(product.batches) == 1
    batch = product.batches[0]
    assert batch.reference == batch_reference
    assert batch._allocations == {models.OrderLine(order_id, sku, 1)}


def test_get_product_not_existing(session, random_sku):
    product_repository = repositories.SQLAlchemyProductRepository(session)

    assert product_repository.get(random_sku()) is None
