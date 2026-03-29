from sqlalchemy import orm as sqlalchemy_orm
from sqlalchemy import text

from allocations.adapters import repositories


def insert_batch(reference: str, sku: str, session: sqlalchemy_orm.Session) -> str:
    params = {"reference": reference, "sku": sku}
    session.execute(
        text(
            "INSERT INTO batches (reference, sku, eta, _purchased_quantity)"
            "VALUES (:reference, :sku, NULL, 10)"
        ),
        params,
    )
    return reference


def test_get_product_with_batches(session, random_batch_ref, random_sku):
    sku = random_sku()
    batch_1_ref = insert_batch(random_batch_ref(), sku, session)
    batch_2_ref = insert_batch(random_batch_ref(), sku, session)
    product_repository = repositories.SQLAlchemyProductRepository(session)

    product = product_repository.get(sku)

    assert product is not None
    assert len(product.batches) == 2
    batches_refs = [batch.reference for batch in product.batches]
    assert batch_1_ref in batches_refs
    assert batch_2_ref in batches_refs


def test_get_unknown_sku_returns_none(session, random_sku):
    product_repository = repositories.SQLAlchemyProductRepository(session)

    assert product_repository.get(random_sku()) is None
