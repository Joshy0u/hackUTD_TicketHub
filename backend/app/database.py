from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from contextlib import contextmanager
from dotenv import load_dotenv
import os

# --- Load environment variables ---
load_dotenv()

# --- Database Configuration ---
DB_HOST = os.getenv("DB_HOST", "database-1.csfc6cuael0m.us-east-1.rds.amazonaws.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# PostgreSQL connection URL
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- SQLAlchemy Engine Setup ---
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # refresh stale connections automatically
    echo=True             # set False in production
)

# --- ORM Setup ---
SessionLocal = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

# --- get_db helper function ---
@contextmanager
def get_db():
    """Provide a transactional scope for database operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
