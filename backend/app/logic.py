from datetime import datetime, timedelta, UTC
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from collections import defaultdict

from app.models import LeaveRequest, User, Threshold, LeaveLog, LeaveBalance
from app.email_utils import send_leave_email, send_manager_email


def get_team_shrinkage(db: Session, team_id: int, date: datetime.date) -> float:
    # Count total associates in the team with role='associate'
    total = db.query(User).filter(User.team_id == team_id, User.role == 'associate').count()

    # Get all approved leaves overlapping with the date
    leaves = db.query(LeaveRequest).join(User).filter(
        LeaveRequest.start_date <= date,
        LeaveRequest.end_date >= date,
        LeaveRequest.status == 'Approved',
        User.team_id == team_id,
        User.role == 'associate'
    ).all()

    # DEBUG LOGGING
    print(f"\n[DEBUG] Shrinkage on {date} for team {team_id}")
    print(f"Total associates: {total}")
    print(f"Approved leaves on {date}: {len(leaves)}")
    for leave in leaves:
        print(f"  User {leave.user_id} | {leave.start_date} → {leave.end_date} | Half-day: {leave.is_half_day}")

    # Shrinkage calculation
    leave_days = sum(0.5 if leave.is_half_day else 1 for leave in leaves)
    shrinkage_percent = (leave_days / total) * 100 if total > 0 else 0
    print(f"Calculated Shrinkage: {shrinkage_percent:.2f}%")
    
    return shrinkage_percent



def calculate_weekly_shrinkage_with_carry_forward(db: Session, manager_id: int, year: int, month: int):
    teams = db.query(User).filter_by(reports_to_id=manager_id, role="manager").all()
    manager_team_ids = [t.team_id for t in teams if t.team_id]

    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, monthrange(year, month)[1]).date()

    current = start_date
    weeks = []
    while current <= end_date:
        week_end = min(current + timedelta(days=6 - current.weekday()), end_date)
        weeks.append((current, week_end))
        current = week_end + timedelta(days=1)

    week_results = []
    cumulative_used = 0.0
    carry_forward = 0.0
    weekly_target = 15.0
    monthly_target = weekly_target * len(weeks)

    for week_start, week_end in weeks:
        total_associates = db.query(User).filter(User.team_id.in_(manager_team_ids), User.role == "associate").count()
        leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id.in_(manager_team_ids),
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= week_end,
            LeaveRequest.end_date >= week_start
        ).all()

        leave_days = 0.0
        for leave in leaves:
            if leave.is_half_day:
                leave_days += 0.5
            else:
                overlap_start = max(leave.start_date, week_start)
                overlap_end = min(leave.end_date, week_end)
                leave_days += (overlap_end - overlap_start).days + 1

        shrinkage = round((leave_days / total_associates) * 100, 2) if total_associates > 0 else 0.0
        unused = weekly_target - shrinkage if shrinkage < weekly_target else 0.0
        overused = shrinkage - weekly_target if shrinkage > weekly_target else 0.0
        carry_forward += unused - overused
        cumulative_used += shrinkage

        week_results.append({
            "week_range": f"{week_start.isoformat()} to {week_end.isoformat()}",
            "shrinkage": shrinkage,
            "carry_forward": round(carry_forward, 2),
            "status": "Safe" if cumulative_used <= monthly_target else "Overused"
        })

    return {
        "monthly_target": monthly_target,
        "cumulative_used": round(cumulative_used, 2),
        "weeks": week_results,
        "status": "Safe" if cumulative_used <= monthly_target else "Exceeded"
    }


def get_monthly_leave_count(db: Session, user_id: int) -> int:
    month_str = datetime.now(UTC).strftime("%Y-%m")
    record = db.query(Threshold).filter_by(user_id=user_id, month=month_str).first()
    return record.leave_count if record else 0


def increment_monthly_leave(db: Session, user_id: int) -> None:
    month_str = datetime.now(UTC).strftime("%Y-%m")
    record = db.query(Threshold).filter_by(user_id=user_id, month=month_str).first()
    if not record:
        record = Threshold(user_id=user_id, month=month_str, leave_count=1)
        db.add(record)
    else:
        record.leave_count += 1
    db.commit()


def get_leave_balance(db: Session, user_id: int, leave_type: str) -> int:
    record = db.query(LeaveBalance).filter_by(user_id=user_id, leave_type=leave_type).first()
    return record.balance if record else 0


def decrement_leave_balance(db: Session, user_id: int, leave_type: str, days: float) -> bool:
    record = db.query(LeaveBalance).filter_by(user_id=user_id, leave_type=leave_type).first()
    if record and record.balance >= days:
        record.balance -= days
        db.commit()
        return True
    return False


def convert_cl_to_al(leave_type: str, start_date: datetime.date, end_date: datetime.date) -> str:
    leave_days = (end_date - start_date).days + 1
    if leave_type.upper() == "CL" and leave_days > 2:
        return "AL"
    return leave_type


def has_date_overlap(db: Session, user_id: int, start_date: datetime.date, end_date: datetime.date) -> bool:
    return db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status.in_(["Pending", "Approved"]),
        or_(
            and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
            and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
            and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
        )
    ).first() is not None


def process_leave_application(db: Session, data: dict) -> dict:
    user = db.get(User, data['user_id'])
    team_id = user.team_id

    start = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
    end = datetime.strptime(data['end_date'], "%Y-%m-%d").date()
    is_half_day = data.get("is_half_day", False)
    leave_days = 0.5 if is_half_day else (end - start).days + 1

    if has_date_overlap(db, user.id, start, end):
        return {"message": "You already have a leave request for this date range", "status": "error"}

    original_leave_type = data['leave_type']
    leave_type = convert_cl_to_al(original_leave_type, start, end)
    backup_person = data.get("backup_person")
    status = 'Pending'

    exceeds_threshold = get_monthly_leave_count(db, user.id) >= 5
    insufficient_balance = get_leave_balance(db, user.id, leave_type) < leave_days

    shrinkage_exceeded = False
    if not is_half_day:
        for i in range((end - start).days + 1):
            day = start + timedelta(days=i)
            if day.weekday() < 5 and get_team_shrinkage(db, team_id, day) > 10.0:
                shrinkage_exceeded = True
                break

    if leave_type == "Optional" and leave_days > 2:
        status = "Rejected"
    elif leave_type.lower() == "sick":
        status = "Pending"
    elif exceeds_threshold or shrinkage_exceeded or insufficient_balance:
        status = "Pending"
    else:
        status = "Approved"
        increment_monthly_leave(db, user.id)
        decrement_leave_balance(db, user.id, leave_type, leave_days)

    leave = LeaveRequest(
        user_id=user.id,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        status=status,
        backup_person=backup_person,
        is_half_day=is_half_day
    )
    db.add(leave)
    db.commit()

    db.add(LeaveLog(
        leave_request_id=leave.id,
        changed_by=user.username,
        action=status,
        comments=f"Auto decision from system logic (original: {original_leave_type}, final: {leave_type})"
    ))
    db.commit()

    send_leave_email(
        to_email=f"{user.username}@company.com",
        associate_name=user.username,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        status=status,
        backup_name=backup_person
    )

    if status == "Pending":
        manager = db.get(User, user.team.manager_id)
        if manager:
            send_manager_email(
                to_email=f"{manager.username}@company.com",
                associate_name=user.username,
                leave_type=leave_type,
                start_date=start,
                end_date=end,
                backup_name=backup_person
            )

    return {"message": f"Leave {status.lower()} successfully", "leave_id": leave.id}



def decrement_monthly_leave_count(db: Session, user_id: int) -> None:
    month_str = datetime.now(UTC).strftime("%Y-%m")
    record = db.query(Threshold).filter_by(user_id=user_id, month=month_str).first()
    if record and record.leave_count > 0:
        record.leave_count -= 1
        db.commit()

def increment_leave_balance(db: Session, user_id: int, leave_type: str, days: float) -> None:
    record = db.query(LeaveBalance).filter_by(user_id=user_id, leave_type=leave_type).first()
    if record:
        record.balance += days
        db.commit()


def get_next_30_day_shrinkage(db: Session, user_id: int) -> list:
    user = db.get(User, user_id)
    team_id = user.team_id
    today = datetime.now(UTC).date()
    results = []

    total_team_members = db.query(User).filter_by(team_id=team_id).count()

    for i in range(30):
        target_date = today + timedelta(days=i)
        if target_date.weekday() >= 5:
            continue

        approved_leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id == team_id,
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date
        ).all()

        leave_count = sum(0.5 if l.is_half_day else 1 for l in approved_leaves)
        shrinkage = round((leave_count / total_team_members) * 100, 2) if total_team_members else 0
        results.append({
            "date": target_date.isoformat(),
            "shrinkage": shrinkage,
            "status": (
                "Safe" if shrinkage < 6
                else "Tight" if shrinkage <= 10
                else "Overbooked"
            )
        })

def has_date_overlap(db: Session, user_id: int, start_date: datetime.date, end_date: datetime.date) -> bool:
    return db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status.in_(["Pending", "Approved"]),  # ✅ correct filter
        or_(
            and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
            and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
            and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
        )
    ).first() is not None

def soft_delete_leave(db: Session, user_id: int, leave_id: int):
    leave = db.query(LeaveRequest).filter_by(id=leave_id, user_id=user_id).first()
    if not leave or leave.status not in ["Pending", "Approved"]:
        return {"message": "Leave not found or cannot be deleted", "status": "error"}

    leave.status = "Deleted"

    # Revert leave balance and monthly threshold
    leave_days = 0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
    increment_leave_balance(db, user_id, leave.leave_type, leave_days)
    decrement_monthly_leave_count(db, user_id)

    db.add(LeaveLog(
        leave_request_id=leave.id,
        changed_by=leave.user.username,
        action="Deleted",
        comments="Leave marked as deleted by user"
    ))
    db.commit()

    return {"message": "Leave deleted successfully", "status": "success"}

    return results
