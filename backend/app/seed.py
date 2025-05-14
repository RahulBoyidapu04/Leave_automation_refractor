from sqlalchemy.orm import Session
from app.models import User, Team, LeaveBalance
from app.database import SessionLocal, engine
from app.models import Base
print("👉 Seeding to DB at:", engine.url)

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

def seed_team(db: Session):
    if not db.query(Team).first():
        manager = User(username="admin_manager", role="manager")
        manager.set_password("admin123")
        team = Team(name="Alpha Team", manager=manager)
        db.add(team)
        db.commit()
        return team.id
    return db.query(Team).first().id

def seed_users(db: Session, team_id: int):
    users = [
        {"username": "pvikas", "password": "pvikas123", "role": "manager"},
        {"username": "durgang", "password": "durgang123", "role": "associate"},
        {"username": "kshjit", "password": "kshjit123", "role": "associate"},
        {"username": "meljensn", "password": "meljensn123", "role": "associate"},
        {"username": "msanupaw", "password": "msanupaw123", "role": "associate"},
        {"username": "namgarag", "password": "namgarag123", "role": "associate"},
        {"username": "namjagan", "password": "namjagan123", "role": "associate"},
        {"username": "prvlika", "password": "prvlika123", "role": "associate"},
        {"username": "saiktcha", "password": "saiktcha123", "role": "associate"},
        {"username": "spoortir", "password": "spoortir123", "role": "associate"},
        {"username": "yharika", "password": "yharika123", "role": "associate"},
        {"username": "ysharipr", "password": "ysharipr123", "role": "associate"},
        {"username": "zshnreza", "password": "zshnreza123", "role": "associate"},
        {"username": "chaitmn", "password": "chaitmn123", "role": "associate"},
        {"username": "kartox", "password": "kartox123", "role": "associate"},
        {"username": "mohanssb", "password": "mohanssb123", "role": "associate"},
        {"username": "rahulboy", "password": "rahulboy123", "role": "associate"},
        {"username": "ravikrp", "password": "ravikrp123", "role": "associate"},
        {"username": "szkumarp", "password": "szkumarp123", "role": "associate"},
        {"username": "abhishne", "password": "abhishne123", "role": "manager"},
        {"username": "aishhh", "password": "aishhh123", "role": "associate"},
        {"username": "anishlb", "password": "anishlb123", "role": "associate"},
        {"username": "anneshwa", "password": "anneshwa123", "role": "associate"},
        {"username": "asmithrs", "password": "asmithrs123", "role": "associate"},
        {"username": "avarpooj", "password": "avarpooj123", "role": "associate"},
        {"username": "harinivs", "password": "harinivs123", "role": "associate"},
        {"username": "himaredd", "password": "himaredd123", "role": "associate"},
        {"username": "kavibk", "password": "kavibk123", "role": "associate"},
        {"username": "krishxkk", "password": "krishxkk123", "role": "associate"},
        {"username": "kshobi", "password": "kshobi123", "role": "associate"}
    ]

    for u in users:
        if not db.query(User).filter_by(username=u["username"]).first():
            new_user = User(username=u["username"], role=u["role"], team_id=team_id)
            new_user.set_password(u["password"])
            db.add(new_user)
            db.commit()
            print(f"✅ Created user {u['username']} with hashed password")
            for lt in ["AL", "CL", "Sick"]:
                db.add(LeaveBalance(user_id=new_user.id, leave_type=lt, balance=10))
    db.commit()

def seed():
    db = SessionLocal()
    team_id = seed_team(db)
    seed_users(db, team_id)
    db.close()
    print("✅ Dummy data seeded successfully.")

if __name__ == "__main__":
    seed()
