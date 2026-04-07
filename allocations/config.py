import os


def get_postgres(test=False) -> str:
    db_name = os.environ["POSTGRES_DB"]

    if test:
        db_name = f"{db_name}-test"

    return (
        "postgresql+psycopg"
        f"://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}"
        f"@{os.environ["POSTGRES_HOST"]}:{os.environ["POSTGRES_PORT"]}/{db_name}"
    )


def get_postgres_engine_kwargs():
    return {"isolation_level": "REPEATABLE READ"}
