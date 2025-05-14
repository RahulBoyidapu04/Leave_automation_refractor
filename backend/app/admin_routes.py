from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
import calendar
from pydantic import BaseModel
from typing import Optional

from .database import get_db
from .models import User, Team, Threshold, LeaveRequest, LeaveLog, Notification
from .auth import get_current_user
from .logic import (
    process_leave_application, convert_cl_to_al,
    get_next_30_day_shrinkage, get_team_shrinkage,
    calculate_weekly_shrinkage_with_carry_forward
)
from .email_utils import send_leave_email

router = APIRouter(prefix="/admin")

# -------------------- Helpers --------------------
def check_admin(user: User):
    if user.role != "l5":
        raise HTTPException(status_code=403, detail="Only L5 Admins can access this")

# -------------------- Pydantic Models --------------------
class LeaveApplication(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    backup_person: Optional[str] = None

class LeaveEdit(BaseModel):
    leave_type: Optional[str] = None
    start_date: str
    end_date: str
    backup_person: Optional[str] = None

class NotificationInput(BaseModel):
    user_id: int
    message: str

# -------------------- Users --------------------
@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(User).all()

@router.post("/users")
def create_user(user_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    password = user_data.pop("password", None)
    user = User(**user_data)
    if password:
        user.set_password(password)
    else:
        raise HTTPException(status_code=400, detail="Password is required")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.put("/users/{user_id}")
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    password = user_data.pop("password", None)
    for key, value in user_data.items():
        setattr(user, key, value)
    if password:
        user.set_password(password)
    db.commit()
    return user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

# -------------------- Teams --------------------
@router.get("/teams")
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(Team).all()

@router.post("/teams")
def create_team(team_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    team = Team(**team_data)
    db.add(team)
    db.commit()
    return team

@router.put("/teams/{team_id}")
def update_team(team_id: int, team_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    team = db.query(Team).get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    for key, value in team_data.items():
        setattr(team, key, value)
    db.commit()
    return team

@router.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    team = db.query(Team).get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(team)
    db.commit()
    return {"message": "Team deleted"}

# -------------------- Thresholds --------------------
@router.get("/thresholds")
def list_thresholds(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(Threshold).all()

@router.post("/thresholds")
def create_threshold(thresh_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    t = Threshold(**thresh_data)
    db.add(t)
    db.commit()
    return t

@router.put("/thresholds/{threshold_id}")
def update_threshold(threshold_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    t = db.query(Threshold).get(threshold_id)
    if not t:
        raise HTTPException(status_code=404, detail="Threshold not found")
    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    return t

@router.delete("/thresholds/{threshold_id}")
def delete_threshold(threshold_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    t = db.query(Threshold).get(threshold_id)
    if not t:
        raise HTTPException(status_code=404, detail="Threshold not found")
    db.delete(t)
    db.commit()
    return {"message": "Threshold deleted"}

# -------------------- Calendar --------------------
@router.get("/availability/next-30-days")
def get_l5_calendar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "l5":
        raise HTTPException(status_code=403, detail="Only L5 Admins can access this")

    # Step 1: Get all L4 managers who report to this L5
    l4_managers = db.query(User).filter_by(reports_to_id=current_user.id, role="manager").all()
    manager_ids = [m.id for m in l4_managers]

    # Step 2: Get all teams managed by these L4s
    teams = db.query(Team).filter(Team.manager_id.in_(manager_ids)).all()

    today = datetime.today().date()
    response = []

    for i in range(30):
        target_date = today + timedelta(days=i)
        if target_date.weekday() >= 5:  # Skip weekends
            continue

        day_entry = {"date": target_date.isoformat(), "shrinkage_by_team": {}}
        for team in teams:
            total = db.query(User).filter_by(team_id=team.id, role="associate").count()
            on_leave = db.query(LeaveRequest).join(User).filter(
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date,
                LeaveRequest.status == "Approved",
                User.team_id == team.id
            ).count()

            shrinkage = round((on_leave / total) * 100, 2) if total > 0 else 0
            day_entry["shrinkage_by_team"][team.name] = shrinkage

        response.append(day_entry)

    return response

@router.get("/availability/l5-next-30-days")
def get_l5_availability(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "l5":
        raise HTTPException(status_code=403, detail="Only L5s allowed")

    managers = db.query(User).filter_by(reports_to_id=current_user.id, role="manager").all()
    manager_ids = [m.id for m in managers]

    teams = db.query(Team).filter(Team.manager_id.in_(manager_ids)).all()

    today = datetime.today().date()
    result = []

    for i in range(30):
        target_date = today + timedelta(days=i)
        if target_date.weekday() >= 5:
            continue

        day_data = {"date": target_date.isoformat(), "shrinkage_by_team": {}}
        for team in teams:
            total = db.query(User).filter_by(team_id=team.id, role="associate").count()
            on_leave = db.query(LeaveRequest).join(User).filter(
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date,
                LeaveRequest.status == "Approved",
                User.team_id == team.id
            ).count()

            shrink = round((on_leave / total) * 100, 2) if total > 0 else 0
            day_data["shrinkage_by_team"][team.name] = shrink

        result.append(day_data)

    return result

# @router.get("/manager/monthly-shrinkage")
# def get_monthly_carry_forward_report(year: int, month: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     if current_user.role != "manager":
#         raise HTTPException(status_code=403, detail="Unauthorized")
#     return calculate_weekly_shrinkage_with_carry_forward(db, current_user.id, year, month)

@router.get("/me")
def read_profile(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@router.post("/apply-leave")
def apply_leave(data: LeaveApplication, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = data.dict()
    data["user_id"] = current_user.id
    return process_leave_application(db, data)

@router.get("/team-shrinkage")
def get_shrinkage(date_str: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    shrink = get_team_shrinkage(db, current_user.team_id, target_date)
    return {"shrinkage": round(shrink, 2)}

@router.get("/availability/next-30-days")
def get_availability_calendar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_next_30_day_shrinkage(db, current_user.id)