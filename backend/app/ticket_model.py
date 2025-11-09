from sqlalchemy import Column, Integer, String, DateTime, Text, func, Index
from datetime import datetime
from .database import Base  # assuming your Base is defined in database.py

class BadLog(Base):
    __tablename__ = "bad_logs"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # When the log was created (server time)
    logged_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # equivalent to DEFAULT NOW()
        index=True
    )

    # When it was uploaded (optional text timestamp)
    uploadts = Column(Text, nullable=False)

    # Machine / host name
    hostname = Column(Text, nullable=False, index=True)

    # Reason for log (e.g. "BADMEMORY_3") — note: single underscore
    label = Column(Text, nullable=False, index=True)

    # Raw log line content
    log_line = Column(Text, nullable=False)

    # Optional: add index for common lookups
    __table_args__ = (
        Index('idx_badlogs_label_host', 'label', 'hostname'),
    )

    def __repr__(self):
        return f"<BadLog {self.id} - {self.hostname or 'unknown'} - {self.label or 'no_label'}>"

    def to_dict(self):
        """Convert log record to dict (for API responses or JSON serialization)"""
        return {
            "id": self.id,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
            "uploadts": self.uploadts,
            "hostname": self.hostname,
            "label": self.label,
            "log_line": self.log_line,
        }
