import datetime

from allocations.domain import models
from allocations.service_layer import unit_of_work


class InvalidSKUError(Exception):
    pass


def is_valid_sku(sku: str, batches: list[models.Batch]) -> bool:
    return sku in [batch.sku for batch in batches]


def allocate(order_id: str, sku: str, quantity: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = models.OrderLine(order_id, sku, quantity)
    with uow:
        batches = uow.batches.list()

        if not is_valid_sku(line.sku, batches):
            raise InvalidSKUError(f"Invalid sku {line.sku}")

        batch_ref = models.allocate(line, batches)
        uow.commit()

    return batch_ref


def deallocate(order_id: str, sku: str, quantity: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = models.OrderLine(order_id, sku, quantity)

    with uow:
        batches = uow.batches.list()

        if not is_valid_sku(line.sku, batches):
            raise InvalidSKUError(f"Invalid sku {line.sku}")

        batch_ref = models.deallocate(line, batches)
        uow.commit()

    return batch_ref


def add_batch(
    reference: str,
    sku: str,
    purchased_quantity: int,
    eta: datetime.date | None,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    with uow:
        batch = models.Batch(reference, sku, purchased_quantity, eta)
        uow.batches.add(batch)
        uow.commit()
    return reference
