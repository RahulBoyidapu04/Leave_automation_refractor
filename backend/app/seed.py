from sqlalchemy.orm import Session
from app.models import User, Team, LeaveBalance, OptionalLeaveDate
from app.database import SessionLocal, engine, Base
from datetime import date

print("👉 Seeding data into DB at:", engine.url)

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

# Manager-associate mapping from your image
manager_map = {
    "pvikas": [
        "durgang", "kshjit", "meljensn", "msanupaw", "namgarag", "namjagan", "prvlika",
        "saiktcha", "spoortir", "yharika", "ysharipr", "zshnreza", "chaitmn", "kartox",
        "mohanssb", "rahulboy", "ravikrp", "szkumarp"
    ],
    "abhishne": [
        "aishhh", "anishlb", "anneshwa", "asmithrs", "avarpooj", "harinivs", "himaredd",
        "kavibk", "krishxkk", "kshobi", "mirijhan", "mvysh", "nandhipj", "ogsujith",
        "ramithar", "rkaporva", "saaisk", "shhankar"
    ],
    "farnaza": [
        "abmahara", "ajrishi", "arajakhi", "bhagee", "bnvishnu", "darwesho", "dattriya",
        "gausah", "gurmetkr", "jharisat", "lakssuba", "meenadv", "mohinijb", "pauldeb",
        "saidevab", "sheltodj", "shlinish", "sushbar", "vkdileep", "zdineshm"
    ],
    "shrosam": [
        "abhimsr", "agrananc", "ajayezio", "attaneem", "debjsaru", "iamveer", "imaarav",
        "karthkon", "khumahi", "nagmouni", "nikshim", "pranilpa", "rajazon", "rjayaswa",
        "shreedes", "subhakp", "vanmalla", "vargabis", "varunkhu", "waazid"
    ],
    "sunkart": [
        "akshaynd", "alphbabu", "anujitgh", "arfasadi", "chiwhane", "gowdchax", "hritishr",
        "javvadan", "jsahaarc", "mdakshio", "piradivg", "pogdeviv", "prasasum", "sapshams",
        "sidevasa", "snehagk", "sudiskmr", "vijaylk", "xmaddy", "xraj"
    ]
}

# Sample optional leave dates (add as needed)
optional_leave_dates = [
    date(2025, 1, 14),  # Example: Pongal
    date(2025, 3, 17),  # Example: Holi
    date(2025, 8, 15),  # Example: Independence Day
    date(2025, 10, 2),  # Example: Gandhi Jayanti
    date(2025, 11, 1),  # Example: Kannada Rajyotsava
]

def seed_data():
    db = SessionLocal()

    # --- Create L5 users ---
    l5_users = [
        {"username": "l5_1", "password": "l5_1123"},
        {"username": "l5_2", "password": "l5_2123"},
    ]
    l5_ids = []
    for l5 in l5_users:
        user = db.query(User).filter_by(username=l5["username"]).first()
        if not user:
            user = User(username=l5["username"], role="l5")
            user.set_password(l5["password"])
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created L5: {l5['username']}")
        l5_ids.append(user.id)

    # --- Create managers, teams, associates ---
    manager_usernames = list(manager_map.keys())
    for idx, (manager_username, associates) in enumerate(manager_map.items()):
        # Check or create manager user
        manager = db.query(User).filter_by(username=manager_username).first()
        if not manager:
            manager = User(username=manager_username, role="manager")
            manager.set_password(manager_username + "123")
            # Assign reports_to_id to one of the L5s (alternate)
            manager.reports_to_id = l5_ids[idx % len(l5_ids)]
            db.add(manager)
            db.commit()
            db.refresh(manager)
            print(f"✅ Created manager: {manager_username}")
        else:
            # Update reports_to_id if needed
            l5_id = l5_ids[idx % len(l5_ids)]
            if manager.reports_to_id != l5_id:
                manager.reports_to_id = l5_id
                db.commit()
                print(f"  🔄 Updated manager: {manager_username} reports to L5_{(idx % len(l5_ids)) + 1}")

        # Check or create team
        team = db.query(Team).filter_by(manager_id=manager.id).first()
        if not team:
            team = Team(name=f"{manager_username}_team", manager_id=manager.id)
            db.add(team)
            db.commit()
            db.refresh(team)
            print(f"✅ Created team for {manager_username}")

        # Create or update associates
        for assoc in associates:
            user = db.query(User).filter_by(username=assoc).first()
            if not user:
                user = User(username=assoc, role="associate", team_id=team.id, reports_to_id=manager.id)
                user.set_password(assoc + "123")
                db.add(user)
                db.commit()
                print(f"  👤 Created associate: {assoc}")

                # Add leave balances
                for lt in ["AL", "CL", "Sick"]:
                    db.add(LeaveBalance(user_id=user.id, leave_type=lt, balance=10))
                db.commit()
            else:
                # Update manager and team assignment if needed
                updated = False
                if user.reports_to_id != manager.id:
                    user.reports_to_id = manager.id
                    updated = True
                if user.team_id != team.id:
                    user.team_id = team.id
                    updated = True
                if updated:
                    db.commit()
                    print(f"  🔄 Updated associate: {assoc} (manager/team)")

    # --- Force mapping for all associates in DB ---
    # Build reverse mapping: associate -> manager
    assoc_to_manager = {}
    for manager, associates in manager_map.items():
        for assoc in associates:
            assoc_to_manager[assoc] = manager

    # Update all associates in DB to ensure correct mapping
    all_associates = db.query(User).filter_by(role="associate").all()
    for user in all_associates:
        manager_username = assoc_to_manager.get(user.username)
        if manager_username:
            manager = db.query(User).filter_by(username=manager_username).first()
            team = db.query(Team).filter_by(manager_id=manager.id).first()
            updated = False
            if user.reports_to_id != manager.id:
                user.reports_to_id = manager.id
                updated = True
            if user.team_id != team.id:
                user.team_id = team.id
                updated = True
            if updated:
                db.commit()
                print(f"  🔄 Forced update: {user.username} -> {manager_username}")
        else:
            print(f"  ⚠️ {user.username} not in manager_map, not mapped.")

    # Seed optional leave dates
    for ol_date in optional_leave_dates:
        if not db.query(OptionalLeaveDate).filter_by(date=ol_date).first():
            db.add(OptionalLeaveDate(date=ol_date))
            print(f"🌟 Added optional leave date: {ol_date.isoformat()}")
    db.commit()

    db.close()
    print("🎉 All data seeded successfully.")

if __name__ == "__main__":
    seed_data()
