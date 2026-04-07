import datetime
from typing import Any

import dotenv
import sqlalchemy
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import orm as sqlalchemy_orm

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.domain import exceptions, models
from allocations.service_layer import services, unit_of_work


class OrderLine(BaseModel):
    order_id: str
    sku: str
    quantity: int = Field(gt=0)


class BatchReference(BaseModel):
    reference: str


class BatchPartial(BatchReference):
    sku: str
    eta: datetime.date | None


class BatchIn(BatchPartial):
    quantity: int


class BatchOut(BatchPartial):
    available_quantity: int

    @staticmethod
    def from_domain(batch: models.Batch) -> "BatchOut":
        return BatchOut(
            reference=batch.reference,
            sku=batch.sku,
            eta=batch.eta,
            available_quantity=batch.available_quantity,
        )


class Message(BaseModel):
    message: str


def init_app():
    dotenv.load_dotenv()
    engine_kwargs = {"url": config.get_postgres(), **config.get_postgres_engine_kwargs()}
    engine = sqlalchemy.create_engine(**engine_kwargs)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()

    session_maker = sqlalchemy_orm.sessionmaker(engine)
    app = FastAPI()

    @app.post(
        "/allocate",
        status_code=status.HTTP_201_CREATED,
        response_model=BatchReference,
        responses={status.HTTP_400_BAD_REQUEST: {"model": Message}},
    )
    def allocate(order_line: OrderLine) -> Any:
        uow = unit_of_work.SQLAlchemyProductUnitOfWork(session_maker)
        try:
            reference = services.allocate(
                order_line.order_id, order_line.sku, order_line.quantity, uow
            )
        except (exceptions.OutOfStockError, services.InvalidSKUError) as e:
            return JSONResponse({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

        return BatchReference(reference=reference)

    @app.post(
        "/deallocate",
        status_code=status.HTTP_200_OK,
        response_model=BatchReference,
        responses={status.HTTP_400_BAD_REQUEST: {"model": Message}},
    )
    def deallocate(order_line: OrderLine) -> Any:
        uow = unit_of_work.SQLAlchemyProductUnitOfWork(session_maker)
        try:
            reference = services.deallocate(
                order_line.order_id, order_line.sku, order_line.quantity, uow
            )
        except (exceptions.OutOfStockError, services.InvalidSKUError) as e:
            return JSONResponse({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

        return BatchReference(reference=reference)

    @app.post("/add_batch", status_code=status.HTTP_201_CREATED)
    def add_batch(batch: BatchIn) -> BatchOut:
        uow = unit_of_work.SQLAlchemyProductUnitOfWork(session_maker)
        _batch = services.add_batch(batch.reference, batch.sku, batch.quantity, batch.eta, uow)
        return BatchOut.from_domain(_batch)

    return app


app = init_app()
