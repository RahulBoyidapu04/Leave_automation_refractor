import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------- Configuration --------------------
DATABASE_URL = "sqlite:///app/app.db"
ECHO_LOG = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

# -------------------- Engine & Session --------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=ECHO_LOG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -------------------- Dependency --------------------
def get_db():
    """FastAPI dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
