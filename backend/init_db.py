# backend/init_db.py
from app.database import Base, engine
from app import models  # ✅ make sure this imports ALL models (User, LeaveRequest, etc.)

print("📦 Creating all database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Done.")
