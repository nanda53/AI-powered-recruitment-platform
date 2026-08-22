from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL              # single source, key/config in one place

# check_same_thread=False lets FastAPI's threads share the SQLite connection
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False},
                       pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
