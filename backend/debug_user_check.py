from app.database import SessionLocal
from app.models import User

db = SessionLocal()
user = db.query(User).filter_by(username="rahulboy").first()

if user:
    print("✅ User found:", user.username, user.role)
    print("🔐 Hashed password:", user.password_hash)
else:
    print("❌ User not found")

db.close()
