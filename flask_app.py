from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import models
import orm
import repositories


def init_app():
    app = Flask(__name__)

    get_session = sessionmaker(bind=create_engine(config.get_memory_sqlite()))

    @app.route("/allocate", methods=["POST"])
    def allocate_endpoint():
        session = get_session()
        repository = repositories.SQLAlchemyRepository(session)
        batches = repository.list()
        line = models.OrderLine(
            request.json["order_id"], request.json["sku"], request.json["quantity"]
        )

        batch_ref = models.allocate(line, batches)

        # repository.session.commit()

        return jsonify({"batch_ref": batch_ref}), 201

    return app


if __name__ == "__main__":
    orm.start_mappers()
    init_app()
