import datetime

from allocations.adapters import repositories
from allocations.domain import models


class InvalidSKUError(Exception):
    pass


def is_valid_sku(sku: str, batches: list[models.Batch]) -> bool:
    return sku in [batch.sku for batch in batches]


def allocate(
    line: models.OrderLine, repository: repositories.AbstractRepository, session
) -> str:
    batches = repository.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSKUError(f"Invalid sku {line.sku}")

    batch_ref = models.allocate(line, batches)
    session.commit()

    return batch_ref


def deallocate(
    line: models.OrderLine, repository: repositories.AbstractRepository, session
) -> str:
    batches = repository.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSKUError(f"Invalid sku {line.sku}")

    batch_ref = models.deallocate(line, batches)
    session.commit()

    return batch_ref


def add_batch(
    reference: str,
    sku: str,
    purchased_quantity: int,
    eta: datetime.date | None,
    repository: repositories.AbstractRepository,
    session,
) -> models.Batch:
    batch = models.Batch(reference, sku, purchased_quantity, eta)

    repository.add(batch)
    session.commit()

    return batch
