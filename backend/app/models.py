from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    phone_id = Column(String)               # user email or business identifier
    platform = Column(String, default='WhatsApp')
    customer_number = Column(String)         # customer ID (phone, open_id, etc.)
    last_message = Column(Text)
    ai_reply = Column(Text)
    lead_score = Column(String, default='Warm')
    summary = Column(String, default='General Inquiry')
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Fields for follow‑up logic (used by Celery tasks)
    follow_up_count = Column(Integer, default=0)
    last_interaction = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

class MediaVault(Base):
    __tablename__ = 'media_vault'
    id = Column(Integer, primary_key=True)
    label = Column(String)          # e.g., "Welcome Video"
    file_url = Column(String)       # local path or URL
    media_type = Column(String)     # 'image', 'video', 'text'

# Use the same database file as the rest of the project
engine = create_engine("sqlite:///./ai_business_memory.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist (won't alter existing ones)
Base.metadata.create_all(bind=engine)