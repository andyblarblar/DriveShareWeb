import datetime

from sqlmodel import create_engine, SQLModel, Session, select
from ..security.password import password_context

sqlite_file_name = "db.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def prepare_db():
    # Create tables if not exists
    SQLModel.metadata.create_all(engine)

