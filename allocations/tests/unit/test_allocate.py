import datetime

import pytest

from allocations.domain import models

today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
later = today + datetime.timedelta(days=10)


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = models.Batch("in-stock", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = models.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = models.OrderLine("order123", "RETRO-CLOCK", 10)

    models.allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    sku = "MINIMALIST-SPOON"
    base_quantity = 100

    earliest = models.Batch("speedy-batch", sku, base_quantity, eta=today)
    medium = models.Batch("normal-batch", sku, base_quantity, eta=tomorrow)
    latest = models.Batch("slow-batch", sku, base_quantity, eta=later)
    line = models.OrderLine("order123", sku, 10)

    models.allocate(line, [earliest, medium, latest])

    assert earliest.available_quantity == 90
    assert latest.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = models.Batch("in-stock", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = models.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = models.OrderLine("order123", "RETRO-CLOCK", 10)

    allocation = models.allocate(line, [in_stock_batch, shipment_batch])

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = models.Batch("batch1", "SMALL-FORK", 10, eta=today)
    models.allocate(models.OrderLine("order1", "SMALL-FORK", 10), [batch])

    with pytest.raises(models.OutOfStockError, match="SMALL-FORK"):
        models.allocate(models.OrderLine("order2", "SMALL-FORK", 1), [batch])
