import datetime

import pytest

from models import Batch, OrderLine, OutOfStockError, allocate

today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
later = today + datetime.timedelta(days=10)


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = OrderLine("order123", "RETRO-CLOCK", 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    sku = "MINIMALIST-SPOON"
    base_quantity = 100

    earliest = Batch("speedy-batch", sku, base_quantity, eta=today)
    medium = Batch("normal-batch", sku, base_quantity, eta=tomorrow)
    latest = Batch("slow-batch", sku, base_quantity, eta=later)
    line = OrderLine("order123", sku, 10)

    allocate(line, [earliest, medium, latest])

    assert earliest.available_quantity == 90
    assert latest.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = OrderLine("order123", "RETRO-CLOCK", 10)

    allocation = allocate(line, [in_stock_batch, shipment_batch])

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
    allocate(OrderLine("order1", "SMALL-FORK", 10), [batch])

    with pytest.raises(OutOfStockError, match="SMALL-FORK"):
        allocate(OrderLine("order2", "SMALL-FORK", 1), [batch])
