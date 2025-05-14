from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, LeaveRequest
from datetime import date

client = TestClient(app)

def setup_test_user_and_leaves():
    db = SessionLocal()
    # Create user if not exists
    user = db.query(User).filter_by(username="testuser").first()
    if not user:
        user = User(username="testuser", role="user", team_id=1)
        user.set_password("test123")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Add a sample leave on April 10–11 (Week 2)
    existing = db.query(LeaveRequest).filter_by(user_id=user.id).first()
    if not existing:
        leave = LeaveRequest(
            user_id=user.id,
            leave_type="CL",
            start_date=date(2025, 4, 10),
            end_date=date(2025, 4, 11),
            status="Approved"
        )
        db.add(leave)
        db.commit()

    return user.id

def test_leave_pattern_april_week2():
    user_id = setup_test_user_and_leaves()

    response = client.get(f"/manager/associate-leave-pattern?user_id={user_id}&month=April&week=2")

    assert response.status_code == 200
    data = response.json()

    assert "username" in data
    assert "monthly_summary" in data
    assert "leave_dates" in data
    assert "frequent_days" in data

    assert "2025-04-10" in data["leave_dates"] or "2025-04-11" in data["leave_dates"]
