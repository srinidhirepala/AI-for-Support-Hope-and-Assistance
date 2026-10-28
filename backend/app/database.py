import os
from importlib import import_module
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(REPOSITORY_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'asha.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def initialize_database() -> None:
    import_module("app.models")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    migrations = {
        "users": {"password_hash": "VARCHAR(255)"},
        "self_assessments": {"answers": "TEXT"},
    }

    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            if not inspector.has_table(table_name):
                continue

            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, column_type in columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

        if engine.dialect.name == "postgresql":
            embedding_type = connection.execute(
                text(
                    "SELECT udt_name FROM information_schema.columns "
                    "WHERE table_schema = current_schema() "
                    "AND table_name = 'message_embeddings' "
                    "AND column_name = 'embedding'"
                )
            ).scalar_one_or_none()
            if embedding_type == "vector":
                connection.execute(
                    text(
                        "ALTER TABLE message_embeddings "
                        "ALTER COLUMN embedding TYPE TEXT USING embedding::text"
                    )
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()