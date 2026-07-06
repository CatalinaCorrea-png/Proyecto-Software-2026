from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    import db.models  # noqa: registers models with Base
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate():
    from sqlalchemy import text, inspect as sa_inspect

    with engine.connect() as conn:
        # Add missing columns to missions table
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(missions)")).fetchall()]
        for col, definition in [
            ("name",        "TEXT"),
            ("altitude",    "REAL"),
            ("cell_size_m", "REAL"),
        ]:
            if col not in cols:
                conn.execute(text(f"ALTER TABLE missions ADD COLUMN {col} {definition}"))
        conn.commit()

    # If roles/users tables exist with wrong schema, drop and recreate them
    inspector = sa_inspect(engine)
    existing = inspector.get_table_names()

    needs_rebuild = False
    if "users" in existing:
        user_cols = {c["name"] for c in inspector.get_columns("users")}
        if "username" not in user_cols:
            needs_rebuild = True
    if "roles" in existing:
        role_cols = {c["name"] for c in inspector.get_columns("roles")}
        if "name" not in role_cols:
            needs_rebuild = True

    if needs_rebuild:
        import db.models as _m
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS users"))
            conn.execute(text("DROP TABLE IF EXISTS roles"))
            conn.commit()
        Base.metadata.create_all(bind=engine, tables=[_m.Role.__table__, _m.User.__table__])


def seed_db():
    from db.models import Role, User
    from auth.utils import hash_password

    db = SessionLocal()
    try:
        for role_name in ["ADMIN", "USER"]:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
        db.commit()

        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        user_role = db.query(Role).filter(Role.name == "USER").first()

        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role_id=admin_role.id,
            ))
        if not db.query(User).filter(User.username == "user").first():
            db.add(User(
                username="user",
                hashed_password=hash_password("user123"),
                role_id=user_role.id,
            ))
        db.commit()
    finally:
        db.close()
