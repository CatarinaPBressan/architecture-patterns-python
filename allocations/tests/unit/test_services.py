import datetime

import pytest

from allocations.adapters import repositories
from allocations.domain import exceptions, models
from allocations.service_layer import services, unit_of_work


class FakeProductRepository(repositories.AbstractProductRepository):
    _products = set[models.Product]

    def __init__(self, products: list[models.Product]) -> None:
        self._products = set(products)

    def add(self, product: models.Product) -> None:
        self._products.add(product)

    def get(self, sku: str):
        try:
            return next(p for p in self._products if p.sku == sku)
        except StopIteration:
            return None


class FakeProductUnitOfWork(unit_of_work.AbstractProductUnitOfWork):
    def __init__(self) -> None:
        self.products = FakeProductRepository([])
        self.commited = False

    def commit(self):
        self.commited = True

    def rollback(self):
        pass

    @staticmethod
    def for_batch(
        reference: str, sku: str, quantity: int, eta: datetime.date | None
    ) -> "FakeProductUnitOfWork":
        uow = FakeProductUnitOfWork()
        uow.products.add(models.Product(sku, [models.Batch(reference, sku, quantity, eta)]))
        return uow


def test_returns_allocations():
    uow = FakeProductUnitOfWork.for_batch("b1", "COMPLICATED-LAMP", 100, None)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)

    assert result == "b1"


def test_not_enough_stock():
    uow = FakeProductUnitOfWork.for_batch("b1", "COMPLICATED-LAMP", 10, None)

    with pytest.raises(exceptions.OutOfStockError, match="COMPLICATED-LAMP"):
        services.allocate("o1", "COMPLICATED-LAMP", 100, uow)


def test_error_for_invalid_sku():
    uow = FakeProductUnitOfWork.for_batch("b1", "COMPLICATED-LAMP", 100, None)

    with pytest.raises(services.InvalidSKUError, match="NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits():
    uow = FakeProductUnitOfWork.for_batch("b1", "OMINOUS-MIRROR", 100, None)

    services.allocate("o1", "OMINOUS-MIRROR", 10, uow)

    assert uow.commited is True


def test_deallocate_frees_available_quantity():
    uow = FakeProductUnitOfWork.for_batch(
        "b1",
        "BLUE-PLINTH",
        100,
        None,
    )
    product = uow.products.get("BLUE-PLINTH")
    assert product
    batch = product.batches[0]

    services.allocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch.available_quantity == 90

    services.deallocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch.available_quantity == 100


def test_deallocate_deallocates_from_correct_batch():
    uow = FakeProductUnitOfWork()

    batch_1 = services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    batch_2 = services.add_batch("b2", "BLUE-PLINTH", 100, tomorrow, uow)

    services.allocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch_1.available_quantity == 90
    assert batch_2.available_quantity == 100

    services.deallocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch_1.available_quantity == 100
    assert batch_2.available_quantity == 100


def test_deallocate_deallocates_from_matching_sku_batch():
    uow = FakeProductUnitOfWork()

    batch_1 = services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)
    batch_2 = services.add_batch("b2", "RED-SOFA", 100, None, uow)

    services.allocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch_1.available_quantity == 90
    assert batch_2.available_quantity == 100

    services.deallocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch_1.available_quantity == 100
    assert batch_2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    uow = FakeProductUnitOfWork.for_batch("b1", "BLUE-PLINTH", 100, None)

    with pytest.raises(exceptions.UnallocatedError, match="BLUE-PLINTH"):
        services.deallocate("o1", "BLUE-PLINTH", 10, uow)


def test_trying_to_deallocate_non_existing_batch():
    uow = FakeProductUnitOfWork()

    with pytest.raises(services.InvalidSKUError, match="BLUE-PLINTH"):
        services.deallocate("o1", "BLUE-PLINTH", 10, uow)


def test_add_batch():
    uow = FakeProductUnitOfWork()
    batch = services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert batch.reference == "b1"
    assert batch.sku == "CRUNCHY-ARMCHAIR"
    assert batch.available_quantity == 100
    assert batch.eta is None

    product = uow.products.get("CRUNCHY-ARMCHAIR")
    assert product
    assert batch in product.batches

    assert uow.commited


def test_allocation_returns_allocation():
    uow = FakeProductUnitOfWork()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "b1"
