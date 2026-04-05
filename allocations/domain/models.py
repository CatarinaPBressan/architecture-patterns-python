import dataclasses
import datetime

from allocations.domain import exceptions


@dataclasses.dataclass(unsafe_hash=True)
class OrderLine:
    order_id: str
    sku: str
    quantity: int


class Batch:
    reference: str
    sku: str
    eta: datetime.date | None

    _purchased_quantity: int
    _allocations: set[OrderLine]

    def __init__(
        self, reference: str, sku: str, quantity: int, eta: datetime.date | None = None
    ) -> None:
        self.reference = reference
        self.sku = sku
        self.eta = eta

        self._purchased_quantity = quantity
        self._allocations = set()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Batch):
            return False
        return self.reference == value.reference

    def __hash__(self) -> int:
        return hash(self.reference)

    def __gt__(self, other: "Batch") -> bool:
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if self.can_deallocate(line):
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.available_quantity >= line.quantity and self.sku == line.sku

    def can_deallocate(self, line: OrderLine) -> bool:
        return line in self._allocations


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(_batch for _batch in sorted(batches) if _batch.can_allocate(line))
    except StopIteration as e:
        raise exceptions.OutOfStockError(f"Out of stock for sku {line.sku}") from e

    batch.allocate(line)
    return batch.reference


def deallocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(_batch for _batch in sorted(batches) if _batch.can_deallocate(line))
    except StopIteration as e:
        raise exceptions.UnallocatedError(f"No allocations found for sku {line.sku}") from e

    batch.deallocate(line)
    return batch.reference


class Product:
    sku: str
    batches: list[Batch]  # TODO: change to set

    def __init__(self, sku: str, batches: list[Batch], version_number: int = 0) -> None:
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def __hash__(self) -> int:
        return hash(self.sku)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Product):
            return False
        return self.sku == value.sku

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(_batch for _batch in sorted(self.batches) if _batch.can_allocate(line))
        except StopIteration as e:
            raise exceptions.OutOfStockError(f"Out of stock for sku {line.sku}") from e

        batch.allocate(line)
        self.version_number += 1
        return batch.reference

    def deallocate(self, line: OrderLine) -> str:
        try:
            batch = next(_batch for _batch in sorted(self.batches) if _batch.can_deallocate(line))
        except StopIteration as e:
            raise exceptions.UnallocatedError(f"No allocations found for sku {line.sku}") from e

        batch.deallocate(line)
        return batch.reference
