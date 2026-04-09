from datetime import date


def test_add_batch(fastapi_test_client, random_batch_ref, random_sku):
    reference = random_batch_ref()
    sku = random_sku()
    quantity = 10
    today = date.today().isoformat()
    data = {"reference": reference, "sku": sku, "quantity": quantity, "eta": today}

    response = fastapi_test_client.post("/add_batch", json=data)

    assert response.status_code == 201
    assert response.json() == {
        "reference": reference,
        "sku": sku,
        "available_quantity": quantity,
        "eta": today,
    }
