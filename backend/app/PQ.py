from sqlalchemy import Column, Integer, String, DateTime, Enum, Index
from datetime import datetime
from .database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core fields with constraints
    status = Column(
        String(10),
        nullable=False,
        index=True,
        default="Open"
    )
    user = Column(String(50), nullable=False, index=True)
    title = Column(String(50), nullable=False)
    desc = Column(String(255), nullable=False)
    
    # Priority fields
    priorityGiven = Column(
        String(50),
        nullable=False,
        default="Normal",
        index=True
    )
    estimatedPriority = Column(
        Integer,
        default=0,
        index=True
    )
    
    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Add composite index for common queries
    __table_args__ = (
        Index('idx_status_priority', 'status', 'estimatedPriority'),
    )

    def __repr__(self):
        return f"<Ticket {self.id} - {self.user} - {self.estimatedPriority}>"

    def to_dict(self):
        """Convert ticket to dictionary for API responses"""
        return {
            'id': self.id,
            'status': self.status,
            'user': self.user,
            'title': self.title,
            'description': self.desc,
            'priority_given': self.priorityGiven,
            'estimated_priority': self.estimatedPriority,
            'created_at': self.created_at.isoformat()
        }

