import pytest

import models
import repositories
import services


class FakeSession:
    commited: bool = False

    def commit(self):
        self.commited = True


def test_returns_allocations():
    line = models.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = models.Batch("b1", "COMPLICATED-LAMP", 100)
    repo = repositories.FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())

    assert result == "b1"


def test_error_for_invalid_sku():
    line = models.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = models.Batch("b1", "COMPLICATED-LAMP", 100)
    repo = repositories.FakeRepository([batch])

    with pytest.raises(services.InvalidSKU, match="NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = models.OrderLine("o1", "OMINOUS-MIRROR", 10)
    batch = models.Batch("b1", "OMINOUS-MIRROR", 100)
    repo = repositories.FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)

    assert session.commited is True
