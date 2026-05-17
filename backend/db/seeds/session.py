from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class SeedSettings:
    def __init__(self) -> None:
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", "5433"))
        self.user = os.getenv("POSTGRES_USER", "jobmatcher")
        self.password = os.getenv("POSTGRES_PASSWORD", "jobmatcher")
        self.dbname = os.getenv("POSTGRES_DB", "jobmatcher_v2")

    @property
    def sqlalchemy_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        )


def create_seed_engine() -> Engine:
    settings = SeedSettings()
    return create_engine(settings.sqlalchemy_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    engine = create_seed_engine()
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
