from typing import Generator
from sqlmodel import Session, create_engine
from app.settings import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session