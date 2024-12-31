from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import contextlib
from urllib.parse import quote
# Add check_same_thread=False for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    print("database started with sql lite ")
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    print("database started with nottt sql lite ")
    url = settings.DATABASE_URL % quote(settings.DATABASE_PASSWORD)
    engine = create_engine(url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextlib.contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency for FastAPI
def get_db_dependency():
    with get_db() as db:
        yield db

# Function to create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)