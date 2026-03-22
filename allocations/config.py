import os


def get_sqlite(db_name: str | None = None) -> str:
    if not db_name:
        db_name = ":memory:"

    return f"sqlite+pysqlite:///{db_name}"


def get_app_sqlite() -> str:
    return get_sqlite(os.environ["DB_NAME"])
