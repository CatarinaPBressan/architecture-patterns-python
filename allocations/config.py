import os


def get_sqlite(db_name: str | None = None) -> str:
    if not db_name:
        db_name = ":memory:"

    return f"sqlite+pysqlite:///{db_name}"


def get_app_sqlite() -> str:
    return get_sqlite(os.environ["SQLITE_NAME"])


def get_postgres(test=False) -> str:
    db_name = os.environ["POSTGRES_DB"]

    if test:
        db_name = f"{db_name}-test"

    return (
        "postgresql+psycopg"
        f"://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}"
        f"@{os.environ["POSTGRES_HOST"]}:{os.environ["POSTGRES_PORT"]}/{db_name}"
    )
