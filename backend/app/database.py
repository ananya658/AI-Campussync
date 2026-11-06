from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

db_url = settings.DATABASE_URL
# Handle heroku/neon/supabase postgres:// schema alias
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {}

if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production / Neon PostgreSQL settings:
    # pool_pre_ping tests connection liveness before checkout (essential for Neon idle compute scale-down)
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

try:
    engine = create_engine(db_url, **engine_kwargs)
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
