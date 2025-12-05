"""
Plan model for storing diet and exercise plans.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime
from datetime import datetime
from app.database import Base


class Plan(Base):
    """Model for diet and exercise plan items."""
    
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    type = Column(String(10), nullable=False, index=True)  # 'meal' or 'exercise'
    name = Column(String(200), nullable=False)
    calories = Column(Float, nullable=False)
    duration = Column(Integer)  # minutes, for exercise only
    completed = Column(Boolean, default=False)
    actual_duration = Column(Integer)  # actual time spent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
