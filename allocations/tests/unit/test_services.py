import datetime

import pytest

from allocations.adapters import repositories
from allocations.domain import exceptions, models
from allocations.service_layer import services


class FakeSession:
    commited: bool = False

    def commit(self):
        self.commited = True


def test_returns_allocations():
    repo = repositories.FakeRepository.for_batch("b1", "COMPLICATED-LAMP", 100, None)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, FakeSession())

    assert result == "b1"


def test_not_enough_stock():
    repo = repositories.FakeRepository.for_batch("b1", "COMPLICATED-LAMP", 10, None)

    with pytest.raises(exceptions.OutOfStockError, match="COMPLICATED-LAMP"):
        services.allocate("o1", "COMPLICATED-LAMP", 100, repo, FakeSession())


def test_error_for_invalid_sku():
    repo = repositories.FakeRepository.for_batch("b1", "COMPLICATED-LAMP", 100, None)

    with pytest.raises(services.InvalidSKUError, match="NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())


def test_commits():
    repo = repositories.FakeRepository.for_batch("b1", "OMINOUS-MIRROR", 100, None)
    session = FakeSession()

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)

    assert session.commited is True


def test_deallocate_frees_available_quantity():
    repo = repositories.FakeRepository([])
    session = FakeSession()
    batch = services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)

    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)

    assert batch.available_quantity == 90

    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)

    assert batch.available_quantity == 100


def test_deallocate_deallocates_from_correct_batch():
    repo = repositories.FakeRepository([])
    session = FakeSession()
    batch_1 = services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    batch_2 = services.add_batch(
        "b2",
        "BLUE-PLINTH",
        100,
        tomorrow,
        repo,
        session,
    )

    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)

    assert batch_1.available_quantity == 90
    assert batch_2.available_quantity == 100

    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)

    assert batch_1.available_quantity == 100
    assert batch_2.available_quantity == 100


def test_deallocate_deallocates_from_matching_sku_batch():
    repo = repositories.FakeRepository([])
    session = FakeSession()
    batch_1 = services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    batch_2 = services.add_batch("b2", "RED-SOFA", 100, None, repo, session)

    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)

    assert batch_1.available_quantity == 90
    assert batch_2.available_quantity == 100

    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)

    assert batch_1.available_quantity == 100
    assert batch_2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    repo = repositories.FakeRepository.for_batch("b1", "BLUE-PLINTH", 100, None)
    session = FakeSession()

    with pytest.raises(exceptions.UnallocatedError, match="BLUE-PLINTH"):
        services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)


def test_trying_to_deallocate_non_existing_batch():
    repo = repositories.FakeRepository([])
    session = FakeSession()

    with pytest.raises(services.InvalidSKUError, match="BLUE-PLINTH"):
        services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)
