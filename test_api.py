import datetime
import typing
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)


def random_sku():
    return f"SKU {str(uuid.uuid4())[:8]}"


def random_batch_ref():
    return f"BATCH {str(uuid.uuid4())[:8]}"


def random_order_id():
    return f"ORDER {str(uuid.uuid4())[:8]}"


def add_stock(batches: list[tuple[str, str, int, str | None]], session: Session):
    for batch in batches:
        session.execute(
            text(
                "INSERT INTO batches (reference, sku, _purchased_quantity, eta) "
                "VALUES (:reference, :sku, :quantity, :eta)"
            ),
            {
                "reference": batch[0],
                "sku": batch[1],
                "quantity": batch[2],
                "eta": batch[3],
            },
        )


def test_api_returns_allocation(flask_test_client, session):
    sku = random_sku()
    other_sku = random_sku()
    early_batch, later_batch, other_batch = (
        random_batch_ref(),
        random_batch_ref(),
        random_batch_ref(),
    )
    add_stock(
        [
            (later_batch, sku, 100, tomorrow.isoformat()),
            (early_batch, sku, 100, today.isoformat()),
            (other_batch, other_sku, 100, None),
        ],
        session,
    )
    data = {"order_id": random_order_id(), "sku": sku, "quantity": 1}

    response = flask_test_client.post("/allocate", json=data)

    assert response.status_code == 201
    assert response.json["batch_ref"] == early_batch


def test_allocations_are_persisted(flask_test_client, session):
    sku = random_sku()
    batch1, batch2 = (
        random_batch_ref(),
        random_batch_ref(),
    )
    order1, order2 = random_order_id(), random_order_id()
    add_stock(
        [
            (batch1, sku, 100, today.isoformat()),
            (batch2, sku, 100, tomorrow.isoformat()),
        ],
        session,
    )
    line1 = {"order_id": order1, "sku": sku, "quantity": 100}
    line2 = {"order_id": order2, "sku": sku, "quantity": 100}

    response = flask_test_client.post("/allocate", json=line1)
    assert response.status_code == 201
    assert response.json["batch_ref"] == batch1

    response = flask_test_client.post("/allocate", json=line2)
    assert response.status_code == 201
    assert response.json["batch_ref"] == batch2
