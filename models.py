from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class GpsPoint(Base):
    __tablename__ = 'gps_points'

    id = Column(Integer, primary_key=True)
    lat_google = Column(Float, nullable=False)
    lng_google = Column(Float, nullable=False)
    imei = Column(String(15), nullable=False)
    speed = Column(Float)
    signal = Column(DateTime, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create database and tables
engine = create_engine('sqlite:///gps_tracking.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine) 