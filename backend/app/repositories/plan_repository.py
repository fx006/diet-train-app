"""
Repository for Plan model CRUD operations.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.plan import Plan


class PlanRepository:
    """Repository for managing Plan entities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, plan: Plan) -> Plan:
        """Create a new plan item."""
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def get_by_id(self, plan_id: int) -> Optional[Plan]:
        """Get a plan item by ID."""
        return self.db.query(Plan).filter(Plan.id == plan_id).first()
    
    def get_by_date(self, target_date: date) -> List[Plan]:
        """Get all plan items for a specific date."""
        return self.db.query(Plan).filter(Plan.date == target_date).all()
    
    def get_by_date_and_type(self, target_date: date, plan_type: str) -> List[Plan]:
        """Get plan items for a specific date and type (meal or exercise)."""
        return self.db.query(Plan).filter(
            and_(Plan.date == target_date, Plan.type == plan_type)
        ).all()
    
    def get_all(self) -> List[Plan]:
        """Get all plan items."""
        return self.db.query(Plan).all()
    
    def update(self, plan: Plan) -> Plan:
        """Update an existing plan item."""
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def delete(self, plan_id: int) -> bool:
        """Delete a plan item by ID."""
        plan = self.get_by_id(plan_id)
        if plan:
            self.db.delete(plan)
            self.db.commit()
            return True
        return False
    
    def get_date_range(self, start_date: date, end_date: date) -> List[Plan]:
        """Get all plan items within a date range."""
        return self.db.query(Plan).filter(
            and_(Plan.date >= start_date, Plan.date <= end_date)
        ).all()
    
    def get_unique_dates(self) -> List[date]:
        """Get all unique dates that have plan items."""
        results = self.db.query(Plan.date).distinct().order_by(Plan.date.desc()).all()
        return [result[0] for result in results]
