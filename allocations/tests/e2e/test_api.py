import datetime
import uuid

today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)


def random_sku():
    return f"SKU {str(uuid.uuid4())[:8]}"


def random_batch_ref():
    return f"BATCH {str(uuid.uuid4())[:8]}"


def random_order_id():
    return f"ORDER {str(uuid.uuid4())[:8]}"


def add_stock(batches: list[tuple[str, str, int, str | None]], test_client):
    for batch in batches:
        data = {
            "reference": batch[0],
            "sku": batch[1],
            "quantity": batch[2],
            "eta": batch[3],
        }
        test_client.post("/add_batch", json=data)


def test_api_returns_allocation(flask_test_client):
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
        flask_test_client,
    )
    data = {"order_id": random_order_id(), "sku": sku, "quantity": 1}

    response = flask_test_client.post("/allocate", json=data)

    assert response.status_code == 201
    assert response.json["batch_ref"] == early_batch


def test_400_message_for_invalid_sku(flask_test_client):
    sku = random_sku()
    order_id = random_order_id()
    data = {"order_id": order_id, "sku": sku, "quantity": 20}

    response = flask_test_client.post("/allocate", json=data)

    assert response.status_code == 400
    assert response.json["message"] == f"Invalid sku {sku}"


def test_deallocate(flask_test_client):
    sku = random_sku()
    order_1 = random_order_id()
    order_2 = random_order_id()
    batch = random_batch_ref()
    add_stock([(batch, sku, 100, "2025-12-29")], flask_test_client)

    response = flask_test_client.post(
        "/allocate", json={"order_id": order_1, "sku": sku, "quantity": 100}
    )
    assert response.status_code == 201
    assert response.json["batch_ref"] == batch

    # cannot allocate second order
    response = flask_test_client.post(
        "/allocate", json={"order_id": order_2, "sku": sku, "quantity": 100}
    )
    assert response.status_code == 400

    # deallocate
    response = flask_test_client.post(
        "/deallocate",
        json={"order_id": order_1, "sku": sku, "quantity": 100},
    )
    assert response.status_code == 200

    # now we can allocate second order
    response = flask_test_client.post(
        "/allocate", json={"order_id": order_2, "sku": sku, "quantity": 100}
    )
    assert response.status_code == 201
    assert response.json["batch_ref"] == batch
    assert response.json["batch_ref"] == batch


def test_add_batch(flask_test_client):
    reference = random_batch_ref()
    sku = random_sku()
    quantity = 10
    today = datetime.date.today().isoformat()
    data = {"reference": reference, "sku": sku, "quantity": quantity, "eta": today}

    response = flask_test_client.post("/add_batch", json=data)

    assert response.status_code == 201
    assert response.json == {
        "batch": {
            "reference": reference,
            "sku": sku,
            "available_quantity": quantity,
            "eta": today,
        }
    }
