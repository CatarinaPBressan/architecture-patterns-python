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


def test_400_message_for_invalid_sku(flask_test_client, session):
    sku = random_sku()
    order_id = random_order_id()
    data = {"order_id": order_id, "sku": sku, "quantity": 20}

    response = flask_test_client.post("/allocate", json=data)

    assert response.status_code == 400
    assert response.json["message"] == f"Invalid sku {sku}"


# @pytest.mark.usefixtures("postgres_db")
# @pytest.mark.usefixtures("restart_api")
# def test_deallocate():
#     sku, order1, order2 = random_sku(), random_orderid(), random_orderid()
#     batch = random_batchref()
#     post_to_add_batch(batch, sku, 100, "2011-01-02")
#     url = config.get_api_url()
#     # fully allocate
#     r = requests.post(
#         f"{url}/allocate", json={"orderid": order1, "sku": sku, "qty": 100}
#     )
#     assert r.json()["batchid"] == batch

#     # cannot allocate second order
#     r = requests.post(
#         f"{url}/allocate", json={"orderid": order2, "sku": sku, "qty": 100}
#     )
#     assert r.status_code == 400

#     # deallocate
#     r = requests.post(
#         f"{url}/deallocate",
#         json={
#             "orderid": order1,
#             "sku": sku,
#         },
#     )
#     assert r.ok

#     # now we can allocate second order
#     r = requests.post(
#         f"{url}/allocate", json={"orderid": order2, "sku": sku, "qty": 100}
#     )
#     assert r.ok
#     assert r.json()["batchid"] == batch
