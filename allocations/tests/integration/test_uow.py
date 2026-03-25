import datetime

import pytest
from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import text

from allocations.domain import models
from allocations.service_layer import unit_of_work


def insert_batch(
    reference: str,
    sku: str,
    quantity: int,
    eta: datetime.date | None,
    session: sqlalchemy_orm.Session,
) -> None:
    params = {"reference": reference, "sku": sku, "_purchased_quantity": quantity, "eta": eta}
    session.execute(
        text(
            "INSERT INTO batches (reference, sku, eta, _purchased_quantity)"
            "VALUES (:reference, :sku, NULL, 10)"
        ),
        params,
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


def test_uow_can_retrieve_a_batch_and_allocate_to_it(make_session):
    session: sqlalchemy_orm.Session = make_session()
    insert_batch("batch1", "HIPSTER-WORKBENCH", 100, None, session)
    session.commit()

    with unit_of_work.SqlAlchemyUnitOfWork(make_session) as uow:
        batch = uow.batches.get("batch1")
        line = models.OrderLine("o1", "HIPSTER-WORKBENCH", 10)
        batch.allocate(line)
        uow.commit()

    batch_ref = get_allocated_batch_ref("o1", "HIPSTER-WORKBENCH", session)
    assert batch_ref == "batch1"


def test_rolls_back_uncommited_work_by_default(make_session):
    with unit_of_work.SqlAlchemyUnitOfWork(make_session) as uow:
        insert_batch("batch1", "MEDIUM-PLINTH", 100, None, uow.session)

    session = make_session()
    rows = list(session.execute(text("SELECT * FROM 'batches'")))
    assert rows == []


def test_rolls_back_on_error(make_session):
    class TestException(Exception):
        pass

    with pytest.raises(TestException):
        with unit_of_work.SqlAlchemyUnitOfWork(make_session) as uow:
            insert_batch("batch1", "MEDIUM-PLINTH", 100, None, uow.session)
            raise TestException

    session = make_session()
    rows = list(session.execute(text("SELECT * FROM 'batches'")))
    assert rows == []
