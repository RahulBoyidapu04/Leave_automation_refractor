from typing import Literal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from app.models import Base, User, LeaveRequest, LeaveBalance, Threshold
from app.logic import (
    get_leave_balance, decrement_leave_balance,
    get_monthly_leave_count, increment_monthly_leave,
    process_leave_application, get_next_30_day_shrinkage,
    convert_cl_to_al, get_team_shrinkage
)
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, patch

# ---------- Parametrized Test convert_cl_to_al ----------
import pytest

@pytest.mark.parametrize("leave_type,start,end,expected", [
    ("CL", date(2025, 5, 1), date(2025, 5, 2), "CL"),
    ("CL", date(2025, 5, 1), date(2025, 5, 4), "AL"),
    ("AL", date(2025, 5, 1), date(2025, 5, 4), "AL"),
])
def test_convert_cl_to_al_param(leave_type: Literal['CL'] | Literal['AL'], start: date, end: date, expected: Literal['CL'] | Literal['AL']):
    assert convert_cl_to_al(leave_type, start, end) == expected

# ---------- Setup In-Memory Test DB ----------
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def test_user(db: Session):
    user = User(username="testuser", hashed_password="hash", role="associate", team_id=1)


    db.add(user)
    db.commit()
    return user

@pytest.fixture
def setup_leave_balance(db: Session, test_user: User):
    balance = LeaveBalance(user_id=test_user.id, leave_type="AL", balance=10)
    db.add(balance)
    db.commit()
    return balance

@pytest.fixture
def setup_threshold(db: Session, test_user: User):
    threshold = Threshold(user_id=test_user.id, month=datetime.now().strftime("%Y-%m"), leave_count=4)
    db.add(threshold)
    db.commit()
    return threshold

# ---------- Test Leave Balance Logic ----------
def test_get_leave_balance(db: Session, test_user: User, setup_leave_balance: LeaveBalance):
    balance = get_leave_balance(db, test_user.id, "AL")
    assert balance == 10

def test_decrement_leave_balance(db: Session, test_user: User, setup_leave_balance: LeaveBalance):
    success = decrement_leave_balance(db, test_user.id, "AL", 3)
    assert success
    updated = get_leave_balance(db, test_user.id, "AL")
    assert updated == 7

def test_decrement_leave_balance_insufficient(db: Session, test_user: User, setup_leave_balance: LeaveBalance):
    success = decrement_leave_balance(db, test_user.id, "AL", 20)
    assert not success
    updated = get_leave_balance(db, test_user.id, "AL")
    assert updated == 10

# ---------- Test Monthly Threshold Logic ----------
def test_increment_monthly_leave(db: Session, test_user: User, setup_threshold: Threshold):
    increment_monthly_leave(db, test_user.id)
    updated = get_monthly_leave_count(db, test_user.id)
    assert updated == 5

# ---------- Test Leave Approval Logic ----------
def test_process_leave_approval(db: Session, test_user: User, setup_leave_balance: LeaveBalance):
    data = {
        "user_id": test_user.id,
        "leave_type": "AL",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "is_half_day": False,
        "backup_person": "backupuser"
    }
    with patch("app.logic.send_leave_email") as mock_email:
        response = process_leave_application(db, data)
        assert mock_email.called
        assert "leave_id" in response
        assert "approved" in response["message"].lower()

def test_process_leave_rejection_due_to_balance(db: Session, test_user: User):
    # No leave balance set up for this leave type
    data = {
        "user_id": test_user.id,
        "leave_type": "CL",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        "is_half_day": False,
        "backup_person": "backupuser"
    }
    with patch("app.logic.send_leave_email"):
        response = process_leave_application(db, data)
        assert "pending" in response["message"].lower() or "rejected" in response["message"].lower()

def test_process_leave_rejection_due_to_threshold(db: Session, test_user: User, setup_leave_balance: LeaveBalance, setup_threshold: Threshold):
    increment_monthly_leave(db, test_user.id)  # Now leave_count is 5
    data = {
        "user_id": test_user.id,
        "leave_type": "AL",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "is_half_day": False,
        "backup_person": "backupuser"
    }
    with patch("app.logic.send_leave_email"):
        response = process_leave_application(db, data)
        assert "pending" in response["message"].lower() or "rejected" in response["message"].lower()

def test_process_optional_leave_rejection(db: Session, test_user: User, setup_leave_balance: LeaveBalance):
    data = {
        "user_id": test_user.id,
        "leave_type": "Optional",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "is_half_day": False,
        "backup_person": "backupuser"
    }
    with patch("app.logic.send_leave_email"):
        response = process_leave_application(db, data)
        assert "rejected" in response["message"].lower()

# ---------- Test Shrinkage Logic ----------
def test_next_30_day_shrinkage(db: Session, test_user: User):
    shrinkage = get_next_30_day_shrinkage(db, test_user.id)
    assert isinstance(shrinkage, list)
    assert all("date" in entry and "shrinkage" in entry for entry in shrinkage)

# ---------- Mock-based Tests ----------
def test_get_team_shrinkage():
    db = MagicMock()
    db.query(User).filter_by().count.return_value = 10

    query_mock = db.query(LeaveRequest).join().filter()
    query_mock.count.return_value = 2
    db.query(LeaveRequest).join().filter.return_value = query_mock

    shrinkage = get_team_shrinkage(db, team_id=1, date=date(2025, 5, 6))
    assert shrinkage == 20.0

def test_get_leave_balance_with_record():
    db = MagicMock()
    balance_record = LeaveBalance(user_id=1, leave_type="CL", balance=5)
    db.query().filter_by().first.return_value = balance_record

    result = get_leave_balance(db, 1, "CL")
    assert result == 5

def test_get_leave_balance_no_record():
    db = MagicMock()
    db.query().filter_by().first.return_value = None

    result = get_leave_balance(db, 1, "CL")
    assert result == 0