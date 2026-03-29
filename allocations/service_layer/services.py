import datetime

from allocations.domain import models
from allocations.service_layer import unit_of_work


class InvalidSKUError(Exception):
    pass


def allocate(
    order_id: str, sku: str, quantity: int, uow: unit_of_work.AbstractProductUnitOfWork
) -> str:
    line = models.OrderLine(order_id, sku, quantity)
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSKUError(f"Invalid sku {line.sku}")

        batch_ref = product.allocate(line)
        uow.commit()

    return batch_ref


def deallocate(
    order_id: str, sku: str, quantity: int, uow: unit_of_work.AbstractProductUnitOfWork
) -> str:
    line = models.OrderLine(order_id, sku, quantity)
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSKUError(f"Invalid sku {line.sku}")

        batch_ref = product.deallocate(line)
        uow.commit()

    return batch_ref


def add_batch(
    reference: str,
    sku: str,
    purchased_quantity: int,
    eta: datetime.date | None,
    uow: unit_of_work.AbstractProductUnitOfWork,
) -> models.Batch:
    with uow:
        product = uow.products.get(sku)
        if product is None:
            product = models.Product(sku, [])
            uow.products.add(product)
        batch = models.Batch(reference, sku, purchased_quantity, eta)
        product.batches.append(batch)
        uow.commit()
    return batch
