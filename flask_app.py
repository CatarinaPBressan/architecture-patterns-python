from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import models
import orm
import repositories


def init_app(session_maker=None):
    app = Flask(__name__)

    get_session = (
        session_maker
        if session_maker
        else sessionmaker(bind=create_engine(config.get_memory_sqlite()))
    )

    @app.route("/allocate", methods=["POST"])
    def allocate_endpoint():
        session = get_session()
        repository = repositories.SQLAlchemyRepository(session)
        batches = repository.list()
        line = models.OrderLine(
            request.json["order_id"], request.json["sku"], request.json["quantity"]
        )

        if not line.sku in [batch.sku for batch in batches]:
            return jsonify({"message": f"Invalid sku {line.sku}"}), 400

        try:
            batch_ref = models.allocate(line, batches)
        except models.OutOfStockError as e:
            return jsonify({"message": str(e)}), 400

        repository.session.commit()

        return jsonify({"batch_ref": batch_ref}), 201

    return app


if __name__ == "__main__":
    orm.start_mappers()
    init_app()
