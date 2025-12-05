"""
Repository for UserPreference model CRUD operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user_preference import UserPreference


class PreferenceRepository:
    """Repository for managing UserPreference entities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, preference: UserPreference) -> UserPreference:
        """Create a new user preference."""
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        return preference
    
    def get_by_key(self, key: str) -> Optional[UserPreference]:
        """Get a preference by key."""
        return self.db.query(UserPreference).filter(UserPreference.key == key).first()
    
    def get_all(self) -> List[UserPreference]:
        """Get all user preferences."""
        return self.db.query(UserPreference).all()
    
    def update(self, key: str, value: str) -> Optional[UserPreference]:
        """Update a preference value by key."""
        preference = self.get_by_key(key)
        if preference:
            preference.value = value
            self.db.commit()
            self.db.refresh(preference)
            return preference
        return None
    
    def upsert(self, key: str, value: str) -> UserPreference:
        """Create or update a preference."""
        preference = self.get_by_key(key)
        if preference:
            preference.value = value
            self.db.commit()
            self.db.refresh(preference)
        else:
            preference = UserPreference(key=key, value=value)
            preference = self.create(preference)
        return preference
    
    def delete(self, key: str) -> bool:
        """Delete a preference by key."""
        preference = self.get_by_key(key)
        if preference:
            self.db.delete(preference)
            self.db.commit()
            return True
        return False
    
    def delete_all(self) -> int:
        """Delete all preferences. Returns count of deleted items."""
        count = self.db.query(UserPreference).count()
        self.db.query(UserPreference).delete()
        self.db.commit()
        return count
