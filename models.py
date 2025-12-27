import dataclasses
import datetime


@dataclasses.dataclass(frozen=True)
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


class NotEnoughStockError(Exception):
    pass
