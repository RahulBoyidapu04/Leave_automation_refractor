from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
import calendar
from pydantic import BaseModel
from typing import Optional, List

from .database import get_db
from .models import User, LeaveRequest, LeaveLog, Notification
from .auth import get_current_user, get_manager_user
from .logic import (
    process_leave_application, convert_cl_to_al,
    get_next_30_day_shrinkage, get_team_shrinkage,
    calculate_weekly_shrinkage_with_carry_forward
)
from .email_utils import send_leave_email
import logging

class LeaveDecisionRequest(BaseModel):
    leave_id: int
    decision: str
    comments: str = ""

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Core"])

# ------------------ Models ------------------
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

class LeaveResponse(BaseModel):
    id: int
    leave_type: str
    start_date: str
    end_date: str
    status: str
    backup_person: Optional[str] = None

class ProfileResponse(BaseModel):
    username: str
    role: str

# ------------------ Profile ------------------
@router.get("/me", response_model=ProfileResponse)
def read_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile information"""
    logger.info(f"User {current_user.username} accessed profile")
    return {"username": current_user.username, "role": current_user.role}

# ------------------ Apply Leave ------------------
@router.post("/apply-leave", status_code=status.HTTP_201_CREATED)
def apply_leave(data: LeaveApplication, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Submit a new leave application"""
    try:
        data_dict = data.dict()
        data_dict["user_id"] = current_user.id
        
        logger.info(f"User {current_user.username} applying for {data.leave_type} leave")
        result = process_leave_application(db, data_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error processing leave application: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ------------------ Shrinkage & Calendar ------------------
@router.get("/team-shrinkage")
def get_shrinkage(date_str: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get team shrinkage percentage for a specific date"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        shrink = get_team_shrinkage(db, current_user.team_id, target_date)
        return {"shrinkage": round(shrink, 2)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error calculating shrinkage: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not calculate shrinkage")

@router.get("/availability/next-30-days")
def get_availability_calendar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get availability calendar for the next 30 days"""
    try:
        return get_next_30_day_shrinkage(db, current_user.id)
    except Exception as e:
        logger.error(f"Error getting availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve availability data")

# ------------------ Manager: Associate Leave Pattern ------------------
@router.get("/manager/associates")
def get_associates_for_manager(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all associates under manager's team"""
    if current_user.role != "manager":
        logger.warning(f"Unauthorized access attempt by {current_user.username} to manager endpoint")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    
    associates = db.query(User).filter(User.team_id == current_user.team_id, User.role == "associate").all()
    return [{"id": u.id, "username": u.username} for u in associates]

@router.get("/manager/associate-leave-pattern")
def get_associate_leave_pattern(
    user_id: int, 
    month: str = Query(default="All"), 
    week: str = Query(default="All"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get leave pattern for a specific associate"""
    # Authorization check
    if current_user.role != "manager":
        logger.warning(f"Unauthorized access attempt by {current_user.username} to manager endpoint")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # Validate user exists and belongs to manager's team
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.team_id != current_user.team_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not in your team")

    # Only include approved leaves
    leaves = db.query(LeaveRequest).filter_by(user_id=user.id, status="Approved").all()

    # Month filtering
    month_mapping = {
        "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9,
        "October": 10, "November": 11, "December": 12, "January": 1, "February": 2, "March": 3
    }

    if month != "All":
        month_num = month_mapping.get(month)
        if not month_num:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month")
        leaves = [leave for leave in leaves if leave.start_date.month == month_num]

    # Week filtering
    if week != "All":
        try:
            week_num = int(week)
            leaves = [leave for leave in leaves if (week_num - 1) * 7 < leave.start_date.day <= week_num * 7]
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Week must be a number or 'All'")

    # Process leave data
    leave_dates = []
    summary = defaultdict(int)
    weekday_freq = defaultdict(int)

    for leave in leaves:
        current = leave.start_date
        while current <= leave.end_date:
            iso = current.isoformat()
            leave_dates.append(iso)
            summary[leave.leave_type] += 1
            weekday = calendar.day_name[current.weekday()]
            weekday_freq[weekday] += 1
            current += timedelta(days=1)

    return {
        "username": user.username,
        "monthly_summary": dict(summary),
        "leave_dates": sorted(leave_dates),
        "frequent_days": dict(weekday_freq)
    }

# ------------------ Manager: Pending Leaves ------------------
@router.get("/manager/pending-leaves")
def get_pending_leaves(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all pending leave requests for associates in manager's team"""
    if current_user.role != "manager":
        logger.warning(f"Unauthorized access attempt by {current_user.username} to manager endpoint")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    associates = db.query(User).filter_by(team_id=current_user.team_id, role="associate").all()
    associate_ids = [a.id for a in associates]

    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id.in_(associate_ids),
        LeaveRequest.status == "Pending"
    ).all()

    return [
        {
            "leave_id": l.id,
            "associate": db.query(User).get(l.user_id).username,
            "leave_type": l.leave_type,
            "start_date": l.start_date,
            "end_date": l.end_date,
            "backup_person": l.backup_person,
            "is_half_day": l.is_half_day
        }
        for l in leaves
    ]

# ------------------ Manager: Approve/Reject Leave ------------------


from fastapi import Request

# ------------------ Improved Email Handling Function ------------------
async def send_email_with_error_handling(email_func, *args, **kwargs):
    """Wrapper function to handle email sending errors consistently"""
    try:
        result = email_func(*args, **kwargs)
        if hasattr(result, "__await__"):
            await result  # If email_func is async
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        # Continue execution - email failure shouldn't block API response
        return False

# ------------------ Manager: Approve/Reject Leave with Better Email Handling ------------------
@router.post("/manager/leave-decision")
async def approve_or_reject_leave(
    data: LeaveDecisionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_manager_user)
):
    """Approve or reject a pending leave request"""
    leave_id = data.leave_id
    decision = data.decision
    comments = data.comments

    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.info(f"Processing leave decision. Request ID: {request_id}, Leave ID: {leave_id}, Decision: {decision}")

    leave = db.query(LeaveRequest).get(leave_id)
    if not leave:
        logger.warning(f"Leave not found. ID: {leave_id}, Request ID: {request_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave not found")

    user = db.query(User).get(leave.user_id)
    if not user or user.team_id != current_user.team_id:
        logger.warning(f"Unauthorized leave decision attempt. Manager: {current_user.username}, Leave: {leave_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Leave request not in your team")

    if leave.status != "Pending":
        logger.warning(f"Leave already acted on. ID: {leave_id}, Status: {leave.status}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leave already acted on")

    # Update status
    leave.status = decision
    db.commit()

    # Log the action
    log = LeaveLog(
        leave_request_id=leave.id,
        changed_by=current_user.username,
        action=decision,
        comments=comments or f"{decision} by manager"
    )
    db.add(log)
    db.commit()

    # Notify by email
    email_sent = await send_email_with_error_handling(
        send_leave_email,
        to_email=f"{user.username}@company.com",
        associate_name=user.username,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        status=decision,
        backup_name=leave.backup_person
    )

    # Create in-app notification
    notification = Notification(
        user_id=user.id,
        message=f"Your {leave.leave_type} leave request from {leave.start_date} to {leave.end_date} has been {decision.lower()}."
    )
    db.add(notification)
    db.commit()

    result = {"message": f"Leave {decision.lower()} successfully."}
    if not email_sent:
        result["warning"] = "Notification sent but email delivery failed"

    return result

# ------------------ Leave Summary ------------------
@router.get("/leave/summary")
def get_leave_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get summary of user's leave history"""
    leaves = db.query(LeaveRequest).filter_by(user_id=current_user.id).all()

    summary = defaultdict(int)
    total_days = 0

    for leave in leaves:
        if leave.status in ("Approved", "Cancelled"):
            days = (leave.end_date - leave.start_date).days + 1
            total_days += days
            summary[leave.leave_type] += days

    return {
        "total_days": total_days,
        "by_type": dict(summary),
        "count": len(leaves)
    }

@router.get("/leave/my", response_model=List[LeaveResponse])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Get current user's leave requests with optional filters"""
    query = db.query(LeaveRequest).filter_by(user_id=current_user.id)
    
    # Apply filters if provided
    if status:
        query = query.filter(LeaveRequest.status == status)
    
    if from_date:
        try:
            parsed_from = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(LeaveRequest.start_date >= parsed_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
    
    if to_date:
        try:
            parsed_to = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(LeaveRequest.end_date <= parsed_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
    
    # Execute query and sort results
    leaves = query.order_by(LeaveRequest.start_date.desc()).all()
    
    return [
        {
            "id": l.id,
            "leave_type": l.leave_type,
            "start_date": l.start_date.isoformat(),
            "end_date": l.end_date.isoformat(),
            "status": l.status,
            "backup_person": l.backup_person
        }
        for l in leaves
    ]

@router.get("/manager/monthly-shrinkage")
def get_manager_shrinkage(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weekly shrinkage with carry forward for the manager's team"""
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can access this")
    return calculate_weekly_shrinkage_with_carry_forward(db, current_user.id, year, month)


@router.put("/leave/{leave_id}")
def edit_leave(
    leave_id: int,
    data: LeaveEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(LeaveRequest).get(leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    if leave.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your leave")

    if leave.status not in ("Pending", "Approved"):
        raise HTTPException(status_code=400, detail="Cannot edit this leave")

    leave.leave_type = data.leave_type or leave.leave_type
    leave.start_date = datetime.strptime(data.start_date, "%Y-%m-%d").date()
    leave.end_date = datetime.strptime(data.end_date, "%Y-%m-%d").date()
    leave.backup_person = data.backup_person or leave.backup_person

    db.commit()
    db.add(LeaveLog(
        leave_request_id=leave.id,
        changed_by=current_user.username,
        action="Edited",
        comments="Leave details updated by user"
    ))
    db.commit()

    return {"message": "Leave updated successfully"}

from .logic import decrement_monthly_leave_count, increment_leave_balance

@router.delete("/leave/{leave_id}")
def cancel_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave = db.query(LeaveRequest).get(leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    if leave.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your leave")
    if leave.status not in ("Pending", "Approved"):
        raise HTTPException(status_code=400, detail="Leave cannot be cancelled")

    leave_days = (leave.end_date - leave.start_date).days + 1
    leave.status = "Cancelled"
    db.commit()

    # Reverse monthly count and balance
    decrement_monthly_leave_count(db, leave.user_id)
    increment_leave_balance(db, leave.user_id, leave.leave_type, leave_days)

    db.add(LeaveLog(
        leave_request_id=leave.id,
        changed_by=current_user.username,
        action="Cancelled",
        comments="Cancelled by user"
    ))
    db.commit()

    return {"message": "Leave cancelled successfully"}
