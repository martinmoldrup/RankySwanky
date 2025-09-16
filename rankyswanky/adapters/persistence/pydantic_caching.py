"""
Reads pydantic models and stores them in SQLite database using SQLModel.
Functions for caching and retrieving models from the database.
"""
from typing import Dict, Any, Type
from sqlmodel import SQLModel, Field, create_engine, Session
from rankyswanky.adapters.persistence.caching_models import Document
import pathlib

def clear_database(db_path: str = "documents.db") -> None:
    """Deletes the db file."""
    db_file = pathlib.Path(db_path)
    if db_file.exists():
        db_file.unlink()


def create_schema(db_path: str = "documents.db") -> None:
    """Creates the documents table schema in the SQLite database."""
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)

def save_document_to_db(document: Document, db_path: str = "documents.db") -> None:
    """Saves a Document instance to the SQLite database."""
    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        session.merge(document)
        session.commit()

def get_sqlmodel_by_primary_key(model: Type[SQLModel], primary_key_value: str, db_path: str = "documents.db") -> SQLModel | None:
    """Retrieves a SQLModel instance by its ID from the SQLite database."""
    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        return session.get(model, primary_key_value)

def save_sqlmodels_to_db(models: list[SQLModel], db_path: str = "documents.db") -> None:
    """Saves a list of SQLModel instances to the SQLite database."""
    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        for model in models:
            session.merge(model)
        session.commit()

if __name__ == "__main__":
    dummy_document: Document = Document(
        id="1",
        content="This is a test document.",
        embedding_vector=[0.1, 0.2, 0.3],
        metadata={"author": "John Doe"},
        hash="abc123"
    )
    clear_database()
    create_schema()
    save_document_to_db(dummy_document)
