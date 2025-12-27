import datetime

import pytest

from models import Batch, OrderLine


def make_batch_and_line(sku: str, batch_quantity: int, line_quantity: int):
    return (
        Batch("batch-001", sku, batch_quantity, eta=datetime.date.today()),
        OrderLine("order-123", sku, line_quantity),
    )


def test_allocating_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line("ELEGANT-LAMP", 20, 2)

    assert batch.can_allocate(line)


def test_cannot_allocate_if_avaliable_smaller_than_required():
    batch, line = make_batch_and_line("ELEGANT-LAMP", 2, 20)

    assert batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_than_required():
    batch, line = make_batch_and_line("ELEGANT-LAMP", 20, 20)

    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_are_different():
    batch = Batch("batch-001", "UNCONFORTABLE-CHAIR", 10)
    line = OrderLine("order-123", "EXPENSIVE-TOASTER", 10)

    assert batch.can_allocate(line) is False


def test_can_only_deallocate_allocated_lines():
    batch, line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)

    batch.deallocate(line)

    assert batch.available_quantity == 20


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)

    batch.allocate(line)
    batch.allocate(line)

    assert batch.available_quantity == 18
