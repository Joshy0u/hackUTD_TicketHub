from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Ticket(Base):
    __tablename__= "tickets"


    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False)
    user = Column(String(50), nullable=False)
    title = Column(String(50), nullable=False)
    desc = Column(String(255), nullable=False)
    priorityGiven = Column(String(50), default= "Normal")
    estimatedPriority= Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self): 
        return f"<Ticket{self.id} - {self.user} - {self.estimatedPriority}>"

