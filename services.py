import models
import repositories


class InvalidSKU(Exception):
    pass


def is_valid_sku(sku: str, batches: list[models.Batch]) -> bool:
    return sku in [batch.sku for batch in batches]


def allocate(
    line: models.OrderLine, repo: repositories.AbstractRepository, session
) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSKU(f"Invalid sku {line.sku}")

    batch_ref = models.allocate(line, batches)
    session.commit()

    return batch_ref
