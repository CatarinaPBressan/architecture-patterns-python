import dataclasses
import datetime


@dataclasses.dataclass()
class OrderLine:
    order_id: str
    sku: str
    quantity: int

    def __hash__(self) -> int:
        return hash(self.order_id) + hash(self.sku) + hash(self.quantity)


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
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.available_quantity >= line.quantity and self.sku == line.sku


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(_batch for _batch in sorted(batches) if _batch.can_allocate(line))
    except StopIteration as e:
        raise OutOfStockError(f"Out of stock for sku {line.sku}") from e

    batch.allocate(line)
    return batch.reference


class OutOfStockError(Exception):
    pass
