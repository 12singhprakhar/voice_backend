from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")
DATABASE_URL = "sqlite:///./entries.db"

def now_ist():
    return datetime.now(IST)

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    transcript = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    created_at = Column(DateTime, default=now_ist)
    language=Column(String,nullable=True)

# Create the table automatically if it doesn't exist
Base.metadata.create_all(bind=engine)



