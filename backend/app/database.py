from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(db_url, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    # Fallback to local SQLite if remote PostgreSQL is configured but unreachable
    print(f"Warning: Primary DB connection failed ({e}). Falling back to SQLite.")
    engine = create_engine("sqlite:///./campussync.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
