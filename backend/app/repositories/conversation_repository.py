"""
Repository for AIConversation model CRUD operations.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.ai_conversation import AIConversation


class ConversationRepository:
    """Repository for managing AIConversation entities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, conversation: AIConversation) -> AIConversation:
        """Create a new conversation message."""
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_by_id(self, conversation_id: int) -> Optional[AIConversation]:
        """Get a conversation message by ID."""
        return self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id
        ).first()
    
    def get_all(self, limit: Optional[int] = None) -> List[AIConversation]:
        """Get all conversation messages, optionally limited."""
        query = self.db.query(AIConversation).order_by(AIConversation.timestamp)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_recent(self, limit: int = 50) -> List[AIConversation]:
        """Get recent conversation messages."""
        return self.db.query(AIConversation).order_by(
            desc(AIConversation.timestamp)
        ).limit(limit).all()
    
    def get_by_role(self, role: str) -> List[AIConversation]:
        """Get all messages by role (user or assistant)."""
        return self.db.query(AIConversation).filter(
            AIConversation.role == role
        ).order_by(AIConversation.timestamp).all()
    
    def get_after_timestamp(self, timestamp: datetime) -> List[AIConversation]:
        """Get all messages after a specific timestamp."""
        return self.db.query(AIConversation).filter(
            AIConversation.timestamp > timestamp
        ).order_by(AIConversation.timestamp).all()
    
    def delete_all(self) -> int:
        """Delete all conversation messages. Returns count of deleted items."""
        count = self.db.query(AIConversation).count()
        self.db.query(AIConversation).delete()
        self.db.commit()
        return count
    
    def delete_before_timestamp(self, timestamp: datetime) -> int:
        """Delete messages before a specific timestamp. Returns count of deleted items."""
        count = self.db.query(AIConversation).filter(
            AIConversation.timestamp < timestamp
        ).count()
        self.db.query(AIConversation).filter(
            AIConversation.timestamp < timestamp
        ).delete()
        self.db.commit()
        return count
