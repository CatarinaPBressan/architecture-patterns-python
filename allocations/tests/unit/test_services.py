import datetime

import pytest

from allocations.domain import exceptions
from allocations.service_layer import services, unit_of_work


class FakeSession:
    commited: bool = False

    def commit(self):
        self.commited = True


def test_returns_allocations():
    uow = unit_of_work.FakeUnitOfWork.for_batch("b1", "COMPLICATED-LAMP", 100, None)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)

    assert result == "b1"


def test_not_enough_stock():
    uow = unit_of_work.FakeUnitOfWork.for_batch("b1", "COMPLICATED-LAMP", 10, None)

    with pytest.raises(exceptions.OutOfStockError, match="COMPLICATED-LAMP"):
        services.allocate("o1", "COMPLICATED-LAMP", 100, uow)


def test_error_for_invalid_sku():
    uow = unit_of_work.FakeUnitOfWork.for_batch("b1", "COMPLICATED-LAMP", 100, None)

    with pytest.raises(services.InvalidSKUError, match="NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits():
    uow = unit_of_work.FakeUnitOfWork.for_batch("b1", "OMINOUS-MIRROR", 100, None)

    services.allocate("o1", "OMINOUS-MIRROR", 10, uow)

    assert uow.commited is True


def test_deallocate_frees_available_quantity():
    uow = unit_of_work.FakeUnitOfWork()
    batch = services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)

    services.allocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch.available_quantity == 90

    services.deallocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch.available_quantity == 100


def test_deallocate_deallocates_from_correct_batch():
    uow = unit_of_work.FakeUnitOfWork()

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
    uow = unit_of_work.FakeUnitOfWork()

    batch_1 = services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)
    batch_2 = services.add_batch("b2", "RED-SOFA", 100, None, uow)

    services.allocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch_1.available_quantity == 90
    assert batch_2.available_quantity == 100

    services.deallocate("o1", "BLUE-PLINTH", 10, uow)

    assert batch_1.available_quantity == 100
    assert batch_2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    uow = unit_of_work.FakeUnitOfWork.for_batch("b1", "BLUE-PLINTH", 100, None)

    with pytest.raises(exceptions.UnallocatedError, match="BLUE-PLINTH"):
        services.deallocate("o1", "BLUE-PLINTH", 10, uow)


def test_trying_to_deallocate_non_existing_batch():
    uow = unit_of_work.FakeUnitOfWork()

    with pytest.raises(services.InvalidSKUError, match="BLUE-PLINTH"):
        services.deallocate("o1", "BLUE-PLINTH", 10, uow)


def test_add_batch():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.commited


def test_allocation_returns_allocation():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "b1"
