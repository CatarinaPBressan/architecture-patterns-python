import datetime
from typing import Annotated, Any

import dotenv
import sqlalchemy
import sqlalchemy.exc
from fastapi import Depends, FastAPI, status
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
    quantity: int = Field(gt=0)


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


def session_maker():
    dotenv.load_dotenv()
    engine_kwargs = {"url": config.get_postgres(), **config.get_postgres_engine_kwargs()}
    engine = sqlalchemy.create_engine(**engine_kwargs)
    try:
        allocations_orm.start_mappers()
    except sqlalchemy.exc.ArgumentError:
        pass

    return sqlalchemy_orm.sessionmaker(engine)


def init_app():
    app = FastAPI()

    @app.post(
        "/allocate",
        status_code=status.HTTP_201_CREATED,
        response_model=BatchReference,
        responses={status.HTTP_400_BAD_REQUEST: {"model": Message}},
    )
    def allocate(
        session_maker: Annotated[
            sqlalchemy_orm.sessionmaker[sqlalchemy_orm.Session], Depends(session_maker)
        ],
        order_line: OrderLine,
    ) -> Any:
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
    def deallocate(
        session_maker: Annotated[
            sqlalchemy_orm.sessionmaker[sqlalchemy_orm.Session], Depends(session_maker)
        ],
        order_line: OrderLine,
    ) -> Any:
        uow = unit_of_work.SQLAlchemyProductUnitOfWork(session_maker)
        try:
            reference = services.deallocate(
                order_line.order_id, order_line.sku, order_line.quantity, uow
            )
        except (exceptions.OutOfStockError, services.InvalidSKUError) as e:
            return JSONResponse({"message": str(e)}, status.HTTP_400_BAD_REQUEST)

        return BatchReference(reference=reference)

    @app.post("/add_batch", status_code=status.HTTP_201_CREATED)
    def add_batch(
        session_maker: Annotated[
            sqlalchemy_orm.sessionmaker[sqlalchemy_orm.Session], Depends(session_maker)
        ],
        batch: BatchIn,
    ) -> BatchOut:
        uow = unit_of_work.SQLAlchemyProductUnitOfWork(session_maker)
        _batch = services.add_batch(batch.reference, batch.sku, batch.quantity, batch.eta, uow)
        return BatchOut.from_domain(_batch)

    return app


app = init_app()
