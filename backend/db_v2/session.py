"""SQLAlchemy engine and session factory for PostgreSQL V2.

Scope: seed tooling and ORM mapping only.
Runtime matching path (matching_v2/) uses psycopg directly and must not import this module.

Connection defaults match the Docker Compose service:
  POSTGRES_HOST=localhost, POSTGRES_PORT=5433,
  POSTGRES_USER=jobmatcher, POSTGRES_PASSWORD=jobmatcher,
  POSTGRES_DB=jobmatcher_v2.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session


def get_v2_engine() -> Engine:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    user = os.getenv("POSTGRES_USER", "jobmatcher")
    password = os.getenv("POSTGRES_PASSWORD", "jobmatcher")
    db = os.getenv("POSTGRES_DB", "jobmatcher_v2")
    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def make_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    if engine is None:
        engine = get_v2_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)
