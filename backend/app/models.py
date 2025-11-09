"""
Reflect existing tables from the database and expose mapped classes.

This module reflects the `bad_logs` table at runtime using SQLAlchemy's
automap. It then monkey-patches a `to_dict` and `__repr__` onto the
reflected mapped class so the rest of the application can use it like a
regular declarative model.

If the table is not present an informative error is raised to help during
development.
"""
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import NoSuchTableError
from .database import engine

# Reflect only the table we care about to keep reflection fast and explicit
metadata = MetaData()
try:
    metadata.reflect(bind=engine, only=["bad_logs"])
except NoSuchTableError:
    raise RuntimeError("Table 'bad_logs' not found in the database during reflection")

Base = automap_base(metadata=metadata)
Base.prepare()

if "bad_logs" not in metadata.tables:
    raise RuntimeError("Table 'bad_logs' not found in reflected metadata")

# The automap class will be available as Base.classes.bad_logs
BadLog = getattr(Base.classes, "bad_logs")

# Add convenience helpers to the reflected class
def badlog_to_dict(self):
    # Convert SQLAlchemy object to dict using its table columns
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}

def badlog_repr(self):
    host = getattr(self, "hostname", None) or "unknown"
    label = getattr(self, "label", None) or "no_label"
    return f"<BadLog {getattr(self, 'id', '?')} - {host} - {label}>"

setattr(BadLog, "to_dict", badlog_to_dict)
setattr(BadLog, "__repr__", badlog_repr)

__all__ = ["Base", "BadLog"]
