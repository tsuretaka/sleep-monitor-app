from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date, time

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) # Store hashed pw
    display_name = Column(String)
    header_user_id = Column(String) # Custom ID for PDF header
    
    logs = relationship("SleepLog", back_populates="user")

class SleepLog(Base):
    __tablename__ = 'sleep_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False) # The target date of the record
    
    sleepiness = Column(Integer) # 1-10
    toilet_count = Column(Integer, default=0)
    memo = Column(Text)
    
    user = relationship("User", back_populates="logs")
    segments = relationship("SleepSegment", back_populates="log", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="log", cascade="all, delete-orphan")

class SleepSegment(Base):
    __tablename__ = 'sleep_segments'
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('sleep_logs.id'), nullable=False)
    
    # Types: 'in_bed', 'deep', 'doze', 'awake'
    segment_type = Column(String, nullable=False) 
    
    # Storing combined datetime or separate time?
    # Spec imply handling crossing midnight. 
    # Storing actual start_at/end_at (DateTime) is safest.
    start_at = Column(String, nullable=False) # ISO format or something convenient
    end_at = Column(String, nullable=False)
    
    log = relationship("SleepLog", back_populates="segments")

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('sleep_logs.id'), nullable=False)
    
    # Types: 'medication', 'toilet', 'alcohol', 'caffeine', etc
    event_type = Column(String, nullable=False)
    happened_at = Column(String, nullable=False) # ISO time string
    
    log = relationship("SleepLog", back_populates="events")

# Database Setup
import os

# ... (imports remain)

# Database Setup
# Database URL from environment variable (for Cloud) or local SQLite
database_url = os.getenv('DATABASE_URL', 'sqlite:///sleep_monitor.db')

# Fix for some PaaS (e.g. Heroku, Render) using postgres:// instead of postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={'check_same_thread': False}, echo=False)
else:
    engine = create_engine(database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
