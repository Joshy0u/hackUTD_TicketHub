# init_db.py
from app.database import init_db  # adjust the import to where init_db() lives
from app.ticket_model import Ticket

if __name__ == "__main__":
    print("🔧 Initializing database...")
    init_db()
    print("✅ Tables created successfully!")
