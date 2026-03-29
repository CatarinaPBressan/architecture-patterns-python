import pytest

from allocations.domain import exceptions, models


def test_product_allocate(random_sku, random_batch_ref, random_order_id):
    sku = random_sku()
    batch_ref = random_batch_ref()
    order_line = models.OrderLine(random_order_id(), sku, 1)
    product = models.Product(sku, [models.Batch(batch_ref, sku, 10)])

    assert product.allocate(order_line) == batch_ref


def test_product_out_of_stock(random_sku, random_batch_ref, random_order_id):
    sku = random_sku()
    batch_ref = random_batch_ref()
    order_line = models.OrderLine(random_order_id(), sku, 100)
    product = models.Product(sku, [models.Batch(batch_ref, sku, 10)])

    with pytest.raises(exceptions.OutOfStockError) as e:
        product.allocate(order_line)
        assert sku in str(e)


def test_product_deallocate(random_sku, random_batch_ref, random_order_id):
    sku = random_sku()
    batch_ref = random_batch_ref()
    order_line = models.OrderLine(random_order_id(), sku, 1)
    product = models.Product(sku, [models.Batch(batch_ref, sku, 10)])

    product.allocate(order_line)

    assert batch_ref == product.deallocate(order_line)


def test_product_deallocate_not_found(random_sku, random_batch_ref, random_order_id):
    sku = random_sku()
    order_line = models.OrderLine(random_order_id(), sku, 1)
    product = models.Product(sku, [])

    with pytest.raises(exceptions.UnallocatedError) as e:
        product.deallocate(order_line)
        assert sku in str(e)
