from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import models
import orm
import repositories
import services


def init_app(session_maker=None):
    app = Flask(__name__)

    get_session = (
        session_maker
        if session_maker
        else sessionmaker(bind=create_engine(config.get_memory_sqlite()))
    )

    @app.route("/allocate", methods=["POST"])
    def allocate():
        session = get_session()
        repository = repositories.SQLAlchemyRepository(session)
        line = models.OrderLine(
            request.json["order_id"], request.json["sku"], request.json["quantity"]
        )

        try:
            batch_ref = services.allocate(line, repository, session)
        except (models.OutOfStockError, services.InvalidSKUError) as e:
            return jsonify({"message": str(e)}), 400

        return jsonify({"batch_ref": batch_ref}), 201

    @app.route("/deallocate", methods=["POST"])
    def deallocate():
        session = get_session()
        repository = repositories.SQLAlchemyRepository(session)
        line = models.OrderLine(
            request.json["order_id"], request.json["sku"], request.json["quantity"]
        )

        try:
            batch_ref = services.deallocate(line, repository, session)
        except (models.UnallocatedError, services.InvalidSKUError) as e:
            return jsonify({"message": str(e)}), 400

        return jsonify({"batch_ref": batch_ref}), 200

    return app


if __name__ == "__main__":
    orm.start_mappers()
    init_app()
