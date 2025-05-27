from app.database import SessionLocal
from app.models import User

# Add this at the top of print_associates_and_managers.py
from app.database import engine
print("Using DB at:", engine.url)

db = SessionLocal()

print(f"{'ID':<5} {'Associate':<15} {'Manager ID':<10} {'Manager Username'}")
print("-" * 45)

associates = db.query(User).filter(User.role == 'associate').all()
for user in associates:
    manager = db.query(User).filter(User.id == user.reports_to_id).first() if user.reports_to_id else None
    print(f"{user.id:<5} {user.username:<15} {user.reports_to_id or '':<10} {manager.username if manager else ''}")

db.close()