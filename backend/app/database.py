"""Database setup with SQLAlchemy ORM."""

import logging
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

logger = logging.getLogger(__name__)


# Create engine with SQLite-specific pragmas for write-ahead logging
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def column_exists(connection, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(connection)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def init_db():
    """Create all database tables and apply migrations."""
    import app.models.models  # noqa: F401 - ensure models are imported
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Apply migrations for columns that may have been added since initial creation
    try:
        with engine.connect() as conn:
            # Check if 'actor' column exists in audit_logs table
            if not column_exists(conn, "audit_logs", "actor"):
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN actor VARCHAR(100) DEFAULT 'system'"))
                conn.commit()
                logger.info("Added 'actor' column to audit_logs table")

            # Check if 'injection_attempt_detected' column exists in leads table
            if not column_exists(conn, "leads", "injection_attempt_detected"):
                conn.execute(text("ALTER TABLE leads ADD COLUMN injection_attempt_detected BOOLEAN DEFAULT 0"))
                conn.commit()
                logger.info("Added 'injection_attempt_detected' column to leads table")
    except Exception as e:
        logger.warning(f"Migration check failed (may already be applied): {e}")