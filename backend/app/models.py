from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import NoSuchTableError
from .database import engine

# Reflection
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
