import os
import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, unique=True, nullable=False)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_checked = Column(DateTime, index=True)
    status = Column(String, default="DISCOVERED")  # DISCOVERED, PROBING, LIVE, PARKED, DEAD
    is_indexed = Column(Boolean, default=False)
    check_count = Column(Integer, default=0)
    content_title = Column(String)

    # Index for fast lookup of domains that need checking (older than 10 minutes)
    __table_args__ = (
        Index("ix_check_priority", "last_checked", "status"),
    )


def get_database_url():
    # Vercel workers / local Docker should always override this with Postgres.
    return os.getenv("DATABASE_URL", "sqlite:///./data/rootex_metadata.db")


def get_session():
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()