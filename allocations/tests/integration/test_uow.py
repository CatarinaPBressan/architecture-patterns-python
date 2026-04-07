import datetime
import time
import traceback

import pytest
from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import text

from allocations.domain import models
from allocations.service_layer import unit_of_work


def insert_batch_with_product(
    reference: str,
    sku: str,
    quantity: int,
    eta: datetime.date | None,
    version_number: int,
    session: sqlalchemy_orm.Session,
) -> None:
    session.execute(
        text("INSERT INTO products (sku, version_number)" "VALUES (:sku, :version_number)"),
        {"sku": sku, "version_number": version_number},
    )

    session.execute(
        text(
            "INSERT INTO batches (reference, sku, eta, _purchased_quantity)"
            "VALUES (:reference, :sku, NULL, 10)"
        ),
        {"reference": reference, "sku": sku, "_purchased_quantity": quantity, "eta": eta},
    )


def get_allocated_batch_ref(order_id: str, sku: str, session: sqlalchemy_orm.Session) -> str:
    params = {"order_id": order_id, "sku": sku}
    order_line_id: int = session.scalar(
        text("SELECT id FROM order_lines WHERE order_id= :order_id AND sku= :sku"),
        params,
    )

    batchref = session.scalar(
        text(
            "SELECT b.reference FROM order_lines AS ol JOIN batches AS b ON ol.batch_id = b.id "
            "WHERE ol.id = :order_line_id"
        ),
        {"order_line_id": order_line_id},
    )
    return batchref


def test_uow_can_retrieve_a_product_and_allocate_to_it(make_session):
    with unit_of_work.SQLAlchemyProductUnitOfWork(make_session) as uow:
        uow.products.add(
            models.Product("HIPSTER-WORKBENCH", [models.Batch("batch1", "HIPSTER-WORKBENCH", 100)])
        )
        uow.commit()

    with unit_of_work.SQLAlchemyProductUnitOfWork(make_session) as uow:
        product = uow.products.get("HIPSTER-WORKBENCH")

        assert product

        line = models.OrderLine("o1", "HIPSTER-WORKBENCH", 10)
        batch_ref = product.allocate(line)
        uow.commit()

    assert batch_ref == "batch1"


def test_uow_rolls_back_uncommited_work_by_default(make_session):
    with unit_of_work.SQLAlchemyProductUnitOfWork(make_session) as uow:
        insert_batch_with_product("batch1", "MEDIUM-PLINTH", 100, None, 1, uow.session)

    session = make_session()
    rows = list(session.execute(text('SELECT * FROM "batches"')))
    assert rows == []
    session.rollback()


def test_rolls_back_on_error(make_session):
    class TestException(Exception):
        pass

    with pytest.raises(TestException):
        with unit_of_work.SQLAlchemyProductUnitOfWork(make_session) as uow:
            insert_batch_with_product("batch1", "MEDIUM-PLINTH", 100, None, 1, uow.session)
            raise TestException

    session = make_session()
    rows = list(session.execute(text('SELECT * FROM "batches"')))
    assert rows == []
    session.rollback()


def try_to_allocate(order_id: str, sku: str, exceptions: list[Exception], uow):
    line = models.OrderLine(order_id, sku, 10)
    try:
        product = uow.products.get(sku)
        assert product
        product.allocate(line)
        time.sleep(0.2)
        uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


# def test_concurrent_updates_to_version_are_not_allowed(
#     make_session, random_sku, random_batch_ref, random_order_id
# ):
#     sku = random_sku()
#     batch_ref = random_batch_ref()

#     with unit_of_work.SQLAlchemyProductUnitOfWork(make_session) as uow:
#         session = uow.session
#         insert_batch_with_product(batch_ref, sku, 100, None, 1, session)
#         session.commit()

#         order_id_1 = random_order_id()
#         order_id_2 = random_order_id()

#         exceptions: list[Exception] = []

#         try_to_allocate_1 = lambda: try_to_allocate(order_id_1, sku, exceptions, uow)  # noqa: E731
#         try_to_allocate_2 = lambda: try_to_allocate(order_id_2, sku, exceptions, uow)  # noqa: E731

#         thread_1 = threading.Thread(target=try_to_allocate_1)
#         thread_2 = threading.Thread(target=try_to_allocate_2)

#         thread_1.start()
#         thread_2.start()
#         thread_1.join()
#         thread_2.join()

#         version = session.scalar(
#             text("SELECT version_number FROM products WHERE sku=:sku"), {"sku": sku}
#         )
#         assert version == 2

#         exception = exceptions[0]
#         print(str(exception))

#         orders = list(
#             session.scalar(
#                 text("SELECT id FROM order_lines WHERE sku=:sku"),
#                 {"sku": sku},
#             )
#         )

#         assert len(orders) == 1
