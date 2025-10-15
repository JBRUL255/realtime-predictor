# backend/db.py
import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/aviator.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# create engine (SQLite)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True, index=True)
    room = Column(String, index=True)
    ts = Column(DateTime, default=datetime.utcnow)
    multiplier = Column(Float, nullable=True)
    raw = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
