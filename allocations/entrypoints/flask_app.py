import flask
import sqlalchemy
from sqlalchemy import orm as sqlalchemy_orm

from allocations import config
from allocations.adapters import orm as allocations_orm
from allocations.adapters import repositories
from allocations.domain import models
from allocations.service_layer import services


def init_app(session_maker=None):
    app = flask.Flask(__name__)

    if not session_maker:
        engine = sqlalchemy.create_engine(config.get_app_sqlite())
        session_maker = sqlalchemy_orm.sessionmaker(engine)

    get_session = session_maker

    @app.route("/allocate", methods=["POST"])
    def allocate():
        session = get_session()
        repository = repositories.SQLAlchemyRepository(session)
        current_request = flask.request

        order_id = current_request.json["order_id"]
        sku = current_request.json["sku"]
        quantity = current_request.json["quantity"]

        try:
            batch_ref = services.allocate(order_id, sku, quantity, repository, session)
        except (models.OutOfStockError, services.InvalidSKUError) as e:
            return flask.jsonify({"message": str(e)}), 400

        return flask.jsonify({"batch_ref": batch_ref}), 201

    @app.route("/deallocate", methods=["POST"])
    def deallocate():
        session = get_session()
        repository = repositories.SQLAlchemyRepository(session)
        current_request = flask.request
        line = models.OrderLine(
            current_request.json["order_id"],
            current_request.json["sku"],
            current_request.json["quantity"],
        )

        try:
            batch_ref = services.deallocate(line, repository, session)
        except (models.UnallocatedError, services.InvalidSKUError) as e:
            return flask.jsonify({"message": str(e)}), 400

        return flask.jsonify({"batch_ref": batch_ref}), 200

    return app


def init_flask():
    engine = sqlalchemy.create_engine(config.get_app_sqlite(), echo=True)
    allocations_orm.mapper_registry.metadata.create_all(engine)
    allocations_orm.start_mappers()
    _app = init_app()

    return _app
