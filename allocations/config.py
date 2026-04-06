import os


def get_sqlite(db_name: str | None = None) -> str:
    if not db_name:
        db_name = ":memory:"

    return f"sqlite+pysqlite:///{db_name}"


def get_app_sqlite() -> str:
    return get_sqlite(os.environ["SQLITE_NAME"])


def get_postgres() -> str:
    return (
        "postgresql+psycopg"
        f"://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}"
        f"@{os.environ["POSTGRES_HOST"]}:{os.environ["POSTGRES_PORT"]}/{os.environ["POSTGRES_DB"]}"
    )
