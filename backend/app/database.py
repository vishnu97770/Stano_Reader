from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

SQLITE_URL = f"sqlite:///{DB_DIR}/stano_reader.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def run_migrations() -> None:
    """Apply column additions that `create_all` cannot handle on existing databases."""
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(
                text("ALTER TABLE sessions ADD COLUMN transcript TEXT NOT NULL DEFAULT '[]'")
            )
            conn.commit()
        except Exception:
            pass  # Column already exists — this is expected on repeated starts


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
