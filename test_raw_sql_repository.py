import datetime

import models
import repositories


def test_add():
    today = datetime.date.today()
    raw_sql_repo = repositories.RawSQLRepository()
    batch = models.Batch("ref", "RAW-DESK", 100, today)

    raw_sql_repo.add(batch)
    raw_sql_repo.commit()

    cursor = raw_sql_repo._connection.cursor()

    row = cursor.execute(
        "SELECT reference, sku, purchased_quantity, eta "
        "FROM batches "
        "WHERE reference = ?",
        ("ref",),
    ).fetchone()

    assert row
    assert row[0] == batch.reference
    assert row[1] == batch.sku
    assert row[2] == batch._purchased_quantity
    assert row[3] == batch.eta.isoformat()

    del raw_sql_repo


def test_get():
    today = datetime.date.today()
    raw_sql_repo = repositories.RawSQLRepository()
    batch = models.Batch("ref", "RAW-DESK", 100, today)
    cursor = raw_sql_repo._connection.cursor()
    cursor.execute(
        "INSERT INTO batches "
        "(reference, sku, eta, purchased_quantity) "
        "VALUES (?, ?, ?, ?)",
        (
            batch.reference,
            batch.sku,
            batch.eta.isoformat(),
            batch._purchased_quantity,
        ),
    )
    raw_sql_repo.commit()

    retrieved = raw_sql_repo.get("ref")

    assert retrieved
    assert retrieved == batch
    assert retrieved.reference == batch.reference
    assert retrieved.sku == batch.sku
    assert retrieved.eta == batch.eta
    assert retrieved._purchased_quantity == retrieved._purchased_quantity


def test_list():
    today = datetime.date.today()
    raw_sql_repo = repositories.RawSQLRepository()
    cursor = raw_sql_repo._connection.cursor()
    batch1 = models.Batch("ref1", "RAW-DESK", 100, today)
    cursor.execute(
        "INSERT INTO batches "
        "(reference, sku, eta, purchased_quantity) "
        "VALUES (?, ?, ?, ?)",
        (
            batch1.reference,
            batch1.sku,
            batch1.eta.isoformat(),
            batch1._purchased_quantity,
        ),
    )
    batch2 = models.Batch("ref2", "RAW-DESK", 100, today)
    cursor.execute(
        "INSERT INTO batches "
        "(reference, sku, eta, purchased_quantity) "
        "VALUES (?, ?, ?, ?)",
        (
            batch2.reference,
            batch2.sku,
            batch2.eta.isoformat(),
            batch2._purchased_quantity,
        ),
    )
    raw_sql_repo.commit()

    [retrieved1, retrieved2] = raw_sql_repo.list()

    assert retrieved1 == batch1
    assert retrieved2 == batch2


def test_get_batch_with_allocations():
    today = datetime.date.today()
    reference = "ref1"
    raw_sql_repo = repositories.RawSQLRepository()
    cursor = raw_sql_repo._connection.cursor()
    cursor.execute(
        "INSERT INTO batches "
        "(reference, sku, eta, purchased_quantity) "
        "VALUES (?, ?, ?, ?)",
        (
            reference,
            "RAW-DESK",
            today.isoformat(),
            100,
        ),
    )
    raw_sql_repo.commit()
    row_id = cursor.execute(
        "SELECT id " "FROM batches " "WHERE reference = ?",
        (reference,),
    ).fetchone()
    cursor.execute(
        "INSERT INTO order_lines "
        "(sku, quantity, order_id, batch_id) "
        "VALUES "
        '("RUSTY-SPOON", 10, "order123", ?)',
        row_id,
    )
    raw_sql_repo.commit()

    batch = raw_sql_repo.get(reference)

    assert batch._allocations == {models.OrderLine("order123", "RUSTY-SPOON", 10)}
