import datetime
from typing import Any

import flask
import sqlalchemy
from sqlalchemy import orm as sqlalchemy_orm

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.domain import exceptions
from allocations.service_layer import services, unit_of_work


def init_app(session_maker=None, engine_kwargs: dict[str, Any] | None = None):
    app = flask.Flask(__name__)

    if not session_maker:
        engine = sqlalchemy.create_engine(**engine_kwargs)
        session_maker = sqlalchemy_orm.sessionmaker(engine)

    get_session = session_maker

    @app.route("/allocate", methods=["POST"])
    def allocate():
        current_request = flask.request

        order_id = current_request.json["order_id"]
        sku = current_request.json["sku"]
        quantity = current_request.json["quantity"]

        try:
            uow = unit_of_work.SQLAlchemyProductUnitOfWork(get_session)
            batch_ref = services.allocate(order_id, sku, quantity, uow)
        except (exceptions.OutOfStockError, services.InvalidSKUError) as e:
            return flask.jsonify({"message": str(e)}), 400

        return flask.jsonify({"batch_ref": batch_ref}), 201

    @app.route("/deallocate", methods=["POST"])
    def deallocate():
        current_request = flask.request

        order_id = current_request.json["order_id"]
        sku = current_request.json["sku"]
        quantity = current_request.json["quantity"]

        try:
            uow = unit_of_work.SQLAlchemyProductUnitOfWork(get_session)
            batch_ref = services.deallocate(order_id, sku, quantity, uow)
        except (exceptions.UnallocatedError, services.InvalidSKUError) as e:
            return flask.jsonify({"message": str(e)}), 400

        return flask.jsonify({"batch_ref": batch_ref}), 200

    @app.route("/add_batch", methods=["POST"])
    def add_batch():
        current_request = flask.request

        reference = current_request.json["reference"]
        sku = current_request.json["sku"]
        quantity = current_request.json["quantity"]
        eta = current_request.json.get("eta")
        if eta is not None:
            eta = datetime.date.fromisoformat(eta)

        uow = unit_of_work.SQLAlchemyProductUnitOfWork(get_session)
        batch = services.add_batch(reference, sku, quantity, eta, uow)

        return (
            flask.jsonify(
                {
                    "batch": {
                        "reference": batch.reference,
                        "sku": batch.sku,
                        "available_quantity": batch.available_quantity,
                        "eta": batch.eta.isoformat() if batch.eta else None,
                    }
                }
            ),
            201,
        )

    return app


def init_flask():
    engine_kwargs = {"url": config.get_postgres(), **config.get_postgres_engine_kwargs()}
    engine = sqlalchemy.create_engine(**engine_kwargs)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()
    _app = init_app(engine_kwargs=engine_kwargs)

    return _app
