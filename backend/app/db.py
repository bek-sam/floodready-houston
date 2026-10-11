"""SQLAlchemy setup. SQLite by default; Timescale hypertable if available."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import database_url

log = logging.getLogger("db")
Base = declarative_base()


class Report(Base):
    __tablename__ = "reports"
    # Composite PK incl. created_at so Timescale can partition on it.
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    created_at = Column(DateTime(timezone=True), primary_key=True,
                        default=lambda: datetime.now(timezone.utc))
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    kind = Column(String(40), nullable=False, default="flooded_road")
    depth_in = Column(Float, nullable=True)
    note = Column(String(1000), nullable=True)


class Place(Base):
    __tablename__ = "watch_places"
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    label = Column(String(200), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    lang = Column(String(8), default="en")


class PushSub(Base):
    __tablename__ = "push_subscriptions"
    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    endpoint = Column(Text, unique=True, nullable=False)
    keys = Column(Text, nullable=False)          # JSON {p256dh, auth}
    place_ids = Column(Text, default="[]")       # JSON list
    lang = Column(String(8), default="en")
    last_levels = Column(Text, default="{}")     # JSON {place_id: level}


class GaugeReading(Base):
    __tablename__ = "gauge_readings"
    gauge_id = Column(String(32), primary_key=True)
    t = Column(DateTime(timezone=True), primary_key=True)
    stage_ft = Column(Float, nullable=False)


_engine = None
_Session = None


def get_engine():
    global _engine, _Session
    if _engine is None:
        url = database_url()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=args, pool_pre_ping=True)
        _Session = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_session():
    get_engine()
    return _Session()


def init_db() -> None:
    try:
        eng = get_engine()
        Base.metadata.create_all(eng)
        if eng.dialect.name == "postgresql":
            try:
                for ext_name in ("timescaledb", "vector"):  # best effort; Tiger has both
                    try:
                        with eng.begin() as c:
                            c.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext_name}"))
                    except Exception as e:
                        log.warning("extension %s skipped: %s", ext_name, e)
                with eng.begin() as c:
                    ext = c.execute(text("SELECT 1 FROM pg_extension WHERE extname='timescaledb'")).first()
                    if ext:
                        c.execute(text("SELECT create_hypertable('reports','created_at',if_not_exists=>TRUE,migrate_data=>TRUE)"))
                        c.execute(text("SELECT create_hypertable('gauge_readings','t',if_not_exists=>TRUE,migrate_data=>TRUE)"))
            except Exception as e:  # plain table is fine
                log.warning("hypertable skipped: %s", e)
    except Exception as e:
        log.warning("db init failed: %s", e)
