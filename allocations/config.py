def get_sqlite(db_name: str | None = None) -> str:
    if not db_name:
        db_name = ":memory:"

    return f"sqlite+pysqlite:///{db_name}"
