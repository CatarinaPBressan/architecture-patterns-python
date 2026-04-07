import datetime

from fastapi import FastAPI
from pydantic import BaseModel


class OrderLine(BaseModel):
    order_id: str
    sku: str
    quantity: int


class Batch(BaseModel):
    reference: str
    sku: str
    available_quantity: int
    eta: datetime.datetime


def init_app():
    app = FastAPI()

    @app.post("/allocate")
    def allocate(order_line: OrderLine):

        return (
            Batch(
                reference="123",
                sku=order_line.sku,
                available_quantity=order_line.quantity,
                eta=datetime.datetime.now(),
            ),
            201,
        )

    return app


app = init_app()
