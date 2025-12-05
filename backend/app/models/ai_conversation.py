"""
AI conversation model for storing chat history.
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class AIConversation(Base):
    """Model for AI conversation history."""
    
    __tablename__ = "ai_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
