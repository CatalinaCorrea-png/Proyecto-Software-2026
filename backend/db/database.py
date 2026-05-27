from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./aerosearch.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    import db.models  # noqa: registers models with Base
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate():
    from sqlalchemy import text
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(missions)")).fetchall()]
        for col, definition in [
            ("name",        "TEXT"),
            ("altitude",    "REAL"),
            ("cell_size_m", "REAL"),
            ("user_id",     "INTEGER"),
        ]:
            if col not in cols:
                conn.execute(text(f"ALTER TABLE missions ADD COLUMN {col} {definition}"))
        conn.commit()
