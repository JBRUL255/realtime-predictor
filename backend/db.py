# backend/db.py
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aviator.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(String, unique=False, index=True, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
    multiplier = Column(Float, nullable=True)
    raw = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
