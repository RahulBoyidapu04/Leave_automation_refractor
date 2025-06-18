from datetime import datetime, timedelta, date, UTC
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from app.models import LeaveRequest, User, Threshold, LeaveLog, LeaveBalance
from app.email_utils import send_leave_email, send_manager_email
from typing import Optional, Dict, List, Any, Union
import logging

logger = logging.getLogger(__name__)

# Constants
SHRINKAGE_THRESHOLD = 10.0
PLANNED_SHRINKAGE_THRESHOLD = 7.0
SICK_SHRINKAGE_THRESHOLD = 3.0
WEEKLY_TARGET = 15.0
MONTHLY_LEAVE_LIMIT = 5
SAFE_SHRINKAGE_THRESHOLD = 6.0
OPTIONAL_LEAVE_MAX_DAYS = 2
EMAIL_DOMAIN = "@amazon.com"

class LeaveProcessingError(Exception):
    """Custom exception for leave processing errors"""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present in data"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def parse_safe_date(date_input: Union[str, datetime, date]) -> date:
    """Safely extract date from a string or datetime object."""
    try:
        if isinstance(date_input, str):
            return datetime.strptime(date_input[:10], "%Y-%m-%d").date()
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, date):
            return date_input
        else:
            raise ValueError(f"Invalid date input format: {type(date_input)}")
    except (ValueError, TypeError) as e:
        logger.error(f"Date parsing error: {e}")
        raise ValidationError(f"Invalid date format: {date_input}")

def is_optional_leave_day(db: Session, date: date) -> bool:
    """Check if a date is an optional leave day"""
    try:
        from app.models import OptionalLeaveDate
        return db.query(OptionalLeaveDate).filter_by(date=date).first() is not None
    except Exception as e:
        logger.error(f"Error checking optional leave day: {e}")
        return False

def get_team_shrinkage(db: Session, team_id: int, target_date: date) -> Dict[str, float]:
    """
    Calculate team shrinkage for a specific date, split by planned and sick leaves.
    Returns a dict: {'planned_shrinkage': float, 'sick_shrinkage': float, 'total_shrinkage': float}
    If the date is an optional leave day, planned shrinkage is 0.
    """
    try:
        # If the date is an optional leave day, planned shrinkage should be 0
        if is_optional_leave_day(db, target_date):
            return {'planned_shrinkage': 0.0, 'sick_shrinkage': 0.0, 'total_shrinkage': 0.0}

        total_team_members = db.query(User).filter_by(team_id=team_id, role='associate').count()
        if total_team_members == 0:
            logger.warning(f"No team members found for team {team_id}")
            return {'planned_shrinkage': 0.0, 'sick_shrinkage': 0.0, 'total_shrinkage': 0.0}

        approved_leaves = db.query(LeaveRequest).join(
            User, LeaveRequest.user_id == User.id
        ).filter(
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
            LeaveRequest.status == 'Approved',
            User.team_id == team_id,
            User.role == 'associate'
        ).all()

        planned_leave_days = 0.0
        sick_leave_days = 0.0
        for leave in approved_leaves:
            days = 0.5 if leave.is_half_day else 1.0
            if leave.leave_type.lower() == "sick":
                sick_leave_days += days
            else:
                planned_leave_days += days

        planned_shrinkage = round((planned_leave_days / total_team_members) * 100, 2)
        sick_shrinkage = round((sick_leave_days / total_team_members) * 100, 2)
        total_shrinkage = planned_shrinkage + sick_shrinkage

        return {
            'planned_shrinkage': planned_shrinkage,
            'sick_shrinkage': sick_shrinkage,
            'total_shrinkage': total_shrinkage
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_team_shrinkage: {e}")
        raise LeaveProcessingError(f"Database error calculating team shrinkage: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_team_shrinkage: {e}")
        raise LeaveProcessingError(f"Error calculating team shrinkage: {e}")

def get_manager_dashboard_shrinkage(db: Session, manager_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
    """Sum shrinkage for all teams managed by the manager"""
    try:
        if target_date is None:
            target_date = datetime.now().date()
        
        manager = db.get(User, manager_id)
        if not manager or manager.role != 'manager':
            return {
                "date": target_date.isoformat(),
                "shrinkage": 0.0,
                "availability": 100.0,
                "status": "Error",
                "error": "Manager not found"
            }
        
        # Get all unique team_ids for associates reporting to this manager
        team_ids = db.query(User.team_id).filter(
            User.reports_to_id == manager_id,
            User.role == 'associate',
            User.team_id.isnot(None)
        ).distinct().all()
        team_ids = [tid[0] for tid in team_ids]
        
        total_shrinkage = 0.0
        for team_id in team_ids:
            shrinkage_dict = get_team_shrinkage(db, team_id, target_date)
            total_shrinkage += shrinkage_dict.get('total_shrinkage', 0.0)
        
        availability = 100 - total_shrinkage
        return {
            "date": target_date.isoformat(),
            "shrinkage": total_shrinkage,
            "availability": availability,
            "status": (
                "Safe" if total_shrinkage < SAFE_SHRINKAGE_THRESHOLD
                else "Tight" if total_shrinkage <= SHRINKAGE_THRESHOLD
                else "Overbooked"
            )
        }
    except Exception as e:
        logger.error(f"Error in get_manager_dashboard_shrinkage: {e}")
        return {
            "date": target_date.isoformat() if target_date else datetime.now().date().isoformat(),
            "shrinkage": 0.0,
            "availability": 100.0,
            "status": "Error",
            "error": str(e)
        }

def get_dashboard_shrinkage(db: Session, team_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
    """Get dashboard shrinkage data with error handling"""
    try:
        if target_date is None:
            target_date = datetime.now().date()

        shrinkage_dict = get_team_shrinkage(db, team_id, target_date)
        total_shrinkage = shrinkage_dict.get('total_shrinkage', 0.0)
        availability = 100 - total_shrinkage

        return {
            "date": target_date.isoformat(),
            "shrinkage": total_shrinkage,
            "availability": availability,
            "status": (
                "Safe" if total_shrinkage < SAFE_SHRINKAGE_THRESHOLD
                else "Tight" if total_shrinkage <= SHRINKAGE_THRESHOLD
                else "Overbooked"
            )
        }
    except Exception as e:
        logger.error(f"Error in get_dashboard_shrinkage: {e}")
        return {
            "date": target_date.isoformat() if target_date else datetime.now().date().isoformat(),
            "shrinkage": 0.0,
            "availability": 100.0,
            "status": "Error",
            "error": str(e)
        }

def get_monthly_shrinkage(db: Session, team_id: int, year: int, month: int) -> float:
    """Calculate monthly shrinkage with improved error handling and optimization"""
    try:
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()

        total_team_members = db.query(User).filter_by(team_id=team_id, role='associate').count()
        if total_team_members == 0:
            logger.warning(f"No team members found for team {team_id}")
            return 0.0

        # Optimized query to get all relevant leaves at once
        approved_leaves = db.query(LeaveRequest).join(
            User, LeaveRequest.user_id == User.id
        ).filter(
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
            LeaveRequest.status == 'Approved',
            User.team_id == team_id,
            User.role == 'associate'
        ).all()

        leave_days = 0.0
        for leave in approved_leaves:
            # Calculate overlap days
            overlap_start = max(leave.start_date, start_date)
            overlap_end = min(leave.end_date, end_date)
            
            if overlap_start <= overlap_end:
                if leave.is_half_day:
                    # For half day, count only if the specific date is within the month
                    if start_date <= leave.start_date <= end_date:
                        leave_days += 0.5
                else:
                    # Full day calculation - count only working days
                    current_date = overlap_start
                    while current_date <= overlap_end:
                        if current_date.weekday() < 5:  # Monday to Friday
                            leave_days += 1.0
                        current_date += timedelta(days=1)

        working_days_in_month = sum(1 for d in range((end_date - start_date).days + 1) 
                                    if (start_date + timedelta(days=d)).weekday() < 5)
        
        if working_days_in_month == 0 or total_team_members == 0:
            return 0.0
            
        return round((leave_days / (total_team_members * working_days_in_month)) * 100, 2)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_monthly_shrinkage: {e}")
        raise LeaveProcessingError(f"Database error calculating monthly shrinkage: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_monthly_shrinkage: {e}")
        raise LeaveProcessingError(f"Error calculating monthly shrinkage: {e}")

def check_monthly_shrinkage_threshold(db: Session, team_id: int, month: int, year: int, 
                                    threshold: float = SHRINKAGE_THRESHOLD) -> bool:
    """Check if monthly shrinkage exceeds threshold with error handling"""
    try:
        shrinkage = get_monthly_shrinkage(db, team_id, year, month)
        return shrinkage > threshold
    except Exception as e:
        logger.error(f"Error checking monthly shrinkage threshold: {e}")
        return False  # Default to safe value

def check_weekly_shrinkage_threshold(db: Session, team_id: int, week_start: date, 
                                   week_end: date, threshold: float = SHRINKAGE_THRESHOLD) -> bool:
    """Check if weekly shrinkage exceeds threshold with improved error handling"""
    try:
        total_associates = db.query(User).filter_by(team_id=team_id, role='associate').count()
        if total_associates == 0:
            logger.warning(f"No associates found for team {team_id}")
            return False

        approved_leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id == team_id,
            User.role == "associate",
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= week_end,
            LeaveRequest.end_date >= week_start
        ).all()

        leave_days = 0.0
        for leave in approved_leaves:
            if leave.is_half_day and leave.start_date == leave.end_date:
                if week_start <= leave.start_date <= week_end:
                    leave_days += 0.5
            else:
                overlap_start = max(leave.start_date, week_start)
                overlap_end = min(leave.end_date, week_end)
                if overlap_start <= overlap_end:
                    # Count only working days
                    current_date = overlap_start
                    while current_date <= overlap_end:
                        if current_date.weekday() < 5:
                            leave_days += 1.0
                        current_date += timedelta(days=1)

        # Calculate working days in the week
        working_days = sum(1 for d in range((week_end - week_start).days + 1) 
                          if (week_start + timedelta(days=d)).weekday() < 5)
        
        if working_days == 0 or total_associates == 0:
            return False
            
        shrinkage = round((leave_days / (total_associates * working_days)) * 100, 2)
        return shrinkage > threshold
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in check_weekly_shrinkage_threshold: {e}")
        return False  # Default to safe value
    except Exception as e:
        logger.error(f"Unexpected error in check_weekly_shrinkage_threshold: {e}")
        return False

def get_fcfs_position(db: Session, user_id: int, month_str: str, timestamp: Optional[datetime] = None) -> int:
    """Get user's position in FCFS queue for the month with error handling"""
    try:
        year, month = map(int, month_str.split('-'))
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()
        
        # Count earlier requests in the same month
        query = db.query(LeaveRequest).filter(
            LeaveRequest.status.in_(['Pending', 'Approved']),
            LeaveRequest.created_at >= datetime.combine(start_date, datetime.min.time()),
            LeaveRequest.created_at <= datetime.combine(end_date, datetime.max.time()),
        )
        
        if timestamp:
            query = query.filter(LeaveRequest.created_at < timestamp)
        
        return query.count() + 1
        
    except (ValueError, SQLAlchemyError) as e:
        logger.error(f"Error getting FCFS position: {e}")
        return 1  # Default to first position

def has_date_overlap(db: Session, user_id: int, start_date: date, end_date: date) -> bool:
    """Check if user has overlapping leave requests with error handling"""
    try:
        return db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_(["Pending", "Approved"]),
            or_(
                and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
            )
        ).first() is not None
        
    except SQLAlchemyError as e:
        logger.error(f"Database error checking date overlap: {e}")
        return True  # Default to safe value (assume overlap)

def get_monthly_leave_count(db: Session, user_id: int) -> int:
    """Get monthly leave count with error handling"""
    try:
        month_str = datetime.now(UTC).strftime("%Y-%m")
        record = db.query(Threshold).filter_by(user_id=user_id, month=month_str).first()
        return record.leave_count if record else 0
    except SQLAlchemyError as e:
        logger.error(f"Database error getting monthly leave count: {e}")
        return 0

def increment_monthly_leave(db: Session, user_id: int) -> None:
    """Increment monthly leave count with error handling"""
    try:
        month_str = datetime.now(UTC).strftime("%Y-%m")
        record = db.query(Threshold).filter_by(user_id=user_id, month=month_str).first()
        if not record:
            record = Threshold(user_id=user_id, month=month_str, leave_count=1)
            db.add(record)
        else:
            record.leave_count += 1
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error incrementing monthly leave: {e}")
        db.rollback()
        raise LeaveProcessingError(f"Failed to increment monthly leave count: {e}")

def get_leave_balance(db: Session, user_id: int, leave_type: str) -> int:
    """Get leave balance with error handling"""
    try:
        record = db.query(LeaveBalance).filter_by(user_id=user_id, leave_type=leave_type).first()
        return record.balance if record else 0
    except SQLAlchemyError as e:
        logger.error(f"Database error getting leave balance: {e}")
        return 0

def decrement_leave_balance(db: Session, user_id: int, leave_type: str, days: float) -> bool:
    """Decrement leave balance with error handling"""
    try:
        record = db.query(LeaveBalance).filter_by(user_id=user_id, leave_type=leave_type).first()
        if record and record.balance >= days:
            record.balance -= days
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        logger.error(f"Database error decrementing leave balance: {e}")
        db.rollback()
        return False

def convert_cl_to_al(leave_type: str, start_date: date, end_date: date) -> str:
    """Convert CL to AL if leave duration exceeds threshold"""
    try:
        leave_days = (end_date - start_date).days + 1
        if leave_type.upper() == "CL" and leave_days > OPTIONAL_LEAVE_MAX_DAYS:
            return "AL"
        return leave_type
    except Exception as e:
        logger.error(f"Error converting leave type: {e}")
        return leave_type  # Return original if conversion fails

def process_leave_application(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """Process leave application with comprehensive error handling, validation, and auto-approval logic"""
    try:
        # Validate required fields
        required_fields = ['user_id', 'leave_type', 'start_date', 'end_date']
        validate_required_fields(data, required_fields)
        
        # Get user with validation
        user = db.get(User, data['user_id'])
        if not user:
            raise ValidationError(f"User not found: {data['user_id']}")
            
        if not user.team_id:
            raise ValidationError("User is not assigned to any team")

        # Parse dates safely
        start = parse_safe_date(data['start_date'])
        end = parse_safe_date(data['end_date'])
        
        # Validate date range
        if start > end:
            raise ValidationError("Start date cannot be after end date")
            
        if start < datetime.now().date():
            raise ValidationError("Cannot apply for leave in the past")

        is_half_day = data.get("is_half_day", False)
        leave_days = 0.5 if is_half_day else (end - start).days + 1

        # Check for date overlap
        if has_date_overlap(db, user.id, start, end):
            return {"message": "You already have a leave request for this date range", "status": "error"}

        # Process leave type conversion
        original_leave_type = data['leave_type']
        leave_type = convert_cl_to_al(original_leave_type, start, end)
        backup_person = data.get("backup_person")
        
        # Initialize status
        status = 'Pending'
        auto_approval_reasons = []
        rejection_reasons = []

        # Check basic validations
        exceeds_monthly_count = get_monthly_leave_count(db, user.id) >= MONTHLY_LEAVE_LIMIT
        insufficient_balance = get_leave_balance(db, user.id, leave_type) < leave_days

        # SPECIAL HANDLING FOR OPTIONAL LEAVE
        if leave_type.lower() == "optional":
            # Check if all dates are optional leave dates
            current = start
            all_optional = True
            while current <= end:
                if not is_optional_leave_day(db, current):
                    all_optional = False
                    break
                current += timedelta(days=1)
            
            if all_optional:
                status = "Approved"
                auto_approval_reasons.append("All dates are designated optional leave days")
            else:
                # For optional leaves on non-optional days, check all constraints
                if exceeds_monthly_count:
                    rejection_reasons.append("Monthly FCFS limit exceeded")
                if insufficient_balance:
                    rejection_reasons.append("Insufficient leave balance")
                    
                if not rejection_reasons:
                    status = "Approved"
                    auto_approval_reasons.append("Optional leave approved within limits")
                    increment_monthly_leave(db, user.id)
                    decrement_leave_balance(db, user.id, leave_type, leave_days)

        # AUTO-APPROVAL LOGIC FOR AL AND CL
        elif leave_type.upper() in ["AL", "CL"]:
            # Check if we can auto-approve based on shrinkage availability
            can_auto_approve = True
            shrinkage_check_passed = True
            
            # Check basic constraints first
            if exceeds_monthly_count:
                rejection_reasons.append("Monthly FCFS limit exceeded")
                can_auto_approve = False
            if insufficient_balance:
                rejection_reasons.append("Insufficient leave balance")
                can_auto_approve = False

            # Check shrinkage constraints for each day
            if can_auto_approve:
                if not is_half_day:
                    current_date = start
                    while current_date <= end and shrinkage_check_passed:
                        if current_date.weekday() < 5:  # Only check working days
                            # Skip optional leave days (shrinkage is auto-zeroed)
                            if is_optional_leave_day(db, current_date):
                                current_date += timedelta(days=1)
                                continue
                                
                            shrinkage = get_team_shrinkage(db, user.team_id, current_date)
                            
                            # For AL/CL, check planned shrinkage threshold
                            if shrinkage['planned_shrinkage'] >= PLANNED_SHRINKAGE_THRESHOLD:
                                rejection_reasons.append(f"Daily planned shrinkage limit exceeded on {current_date.isoformat()}")
                                shrinkage_check_passed = False
                                break
                                
                            # Also check total shrinkage
                            if shrinkage['total_shrinkage'] >= SHRINKAGE_THRESHOLD:
                                rejection_reasons.append(f"Daily total shrinkage limit exceeded on {current_date.isoformat()}")
                                shrinkage_check_passed = False
                                break
                                
                        current_date += timedelta(days=1)
                else:
                    # For half-day leaves, check only the specific date
                    if start.weekday() < 5 and not is_optional_leave_day(db, start):
                        shrinkage = get_team_shrinkage(db, user.team_id, start)
                        if shrinkage['planned_shrinkage'] >= PLANNED_SHRINKAGE_THRESHOLD:
                            rejection_reasons.append("Daily planned shrinkage limit exceeded")
                            shrinkage_check_passed = False
                        elif shrinkage['total_shrinkage'] >= SHRINKAGE_THRESHOLD:
                            rejection_reasons.append("Daily total shrinkage limit exceeded")
                            shrinkage_check_passed = False

            # Check weekly shrinkage if daily checks pass
            if can_auto_approve and shrinkage_check_passed:
                current_week_start = start - timedelta(days=start.weekday())
                current_week_end = current_week_start + timedelta(days=6)
                while current_week_start <= end:
                    if check_weekly_shrinkage_threshold(db, user.team_id, current_week_start, current_week_end):
                        rejection_reasons.append("Weekly shrinkage limit exceeded")
                        shrinkage_check_passed = False
                        break
                    current_week_start += timedelta(days=7)
                    current_week_end += timedelta(days=7)

            # Check monthly shrinkage if weekly checks pass
            if can_auto_approve and shrinkage_check_passed:
                if check_monthly_shrinkage_threshold(db, user.team_id, start.month, start.year):
                    rejection_reasons.append("Monthly shrinkage limit exceeded")
                    shrinkage_check_passed = False

            # Final decision for AL/CL
            if can_auto_approve and shrinkage_check_passed:
                status = "Approved"
                auto_approval_reasons.append("Auto-approved: Shrinkage availability confirmed")
                auto_approval_reasons.append(f"Leave type: {leave_type}")
                
                # Update balances and counts
                increment_monthly_leave(db, user.id)
                decrement_leave_balance(db, user.id, leave_type, leave_days)
            else:
                status = "Pending"

        # SICK LEAVE HANDLING
        elif leave_type.lower() == "sick":
            # Sick leaves have different shrinkage rules
            sick_shrinkage_exceeded = False
            
            if not is_half_day:
                current_date = start
                while current_date <= end:
                    if current_date.weekday() < 5:  # Only check working days
                        if not is_optional_leave_day(db, current_date):
                            shrinkage = get_team_shrinkage(db, user.team_id, current_date)
                            if shrinkage['sick_shrinkage'] >= SICK_SHRINKAGE_THRESHOLD:
                                sick_shrinkage_exceeded = True
                                break
                    current_date += timedelta(days=1)
            else:
                if start.weekday() < 5 and not is_optional_leave_day(db, start):
                    shrinkage = get_team_shrinkage(db, user.team_id, start)
                    if shrinkage['sick_shrinkage'] >= SICK_SHRINKAGE_THRESHOLD:
                        sick_shrinkage_exceeded = True

            # Sick leaves are generally auto-approved unless sick shrinkage is exceeded
            if not sick_shrinkage_exceeded and not exceeds_monthly_count and not insufficient_balance:
                status = "Approved"
                auto_approval_reasons.append("Sick leave auto-approved")
                increment_monthly_leave(db, user.id)
                decrement_leave_balance(db, user.id, leave_type, leave_days)
            else:
                status = "Pending"
                if sick_shrinkage_exceeded:
                    rejection_reasons.append(f"Daily sick shrinkage > {SICK_SHRINKAGE_THRESHOLD}%")
                if exceeds_monthly_count:
                    rejection_reasons.append("Monthly FCFS limit exceeded")
                if insufficient_balance:
                    rejection_reasons.append("Insufficient leave balance")

        # Create leave request
        leave = LeaveRequest(
            user_id=user.id,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            status=status,
            backup_person=backup_person,
            is_half_day=is_half_day,
            applied_on=datetime.now(UTC)
        )

        db.add(leave)
        db.commit()

        # Create detailed log entry
        if status == "Approved" and auto_approval_reasons:
            comments = f"AUTO-APPROVED: {'; '.join(auto_approval_reasons)}"
            if original_leave_type != leave_type:
                comments += f" (converted from {original_leave_type} to {leave_type})"
        elif status == "Pending" and rejection_reasons:
            comments = f"PENDING APPROVAL: {'; '.join(rejection_reasons)}"
            if original_leave_type != leave_type:
                comments += f" (converted from {original_leave_type} to {leave_type})"
        else:
            comments = f"Leave {status.lower()} - standard processing"

        db.add(LeaveLog(
            leave_request_id=leave.id,
            changed_by=user.username,
            action=status,
            comments=comments
        ))
        db.commit()

        # Send notifications
        try:
            send_leave_email(
                to_email=f"{user.username}{EMAIL_DOMAIN}",
                associate_name=user.username,
                leave_type=leave_type,
                start_date=start,
                end_date=end,
                status=status,
                backup_name=backup_person
            )

            # Send manager notification only if pending
            if status == "Pending":
                # Find manager
                manager = None
                if hasattr(user, 'team') and user.team and hasattr(user.team, 'manager_id'):
                    manager = db.get(User, user.team.manager_id)
                elif user.reports_to_id:
                    manager = db.get(User, user.reports_to_id)
                
                if manager:
                    send_manager_email(
                        to_email=f"{manager.username}{EMAIL_DOMAIN}",
                        associate_name=user.username,
                        leave_type=leave_type,
                        start_date=start,
                        end_date=end,
                        backup_name=backup_person
                    )
        except Exception as e:
            logger.error(f"Error sending email notifications: {e}")
            # Don't fail the entire process for email errors

        # Prepare response message
        if status == "Approved":
            if auto_approval_reasons:
                message = f"Leave auto-approved successfully! Reason: {auto_approval_reasons[0]}"
            else:
                message = "Leave approved successfully"
        else:
            message = f"Leave application submitted for manager approval. {'; '.join(rejection_reasons) if rejection_reasons else 'Awaiting manager review.'}"

        return {
            "message": message,
            "leave_id": leave.id,
            "status": "success",
            "leave_status": status,
            "auto_approved": status == "Approved" and bool(auto_approval_reasons)
        }

    except ValidationError as e:
        logger.error(f"Validation error in process_leave_application: {e}")
        return {"message": str(e), "status": "error"}
    except LeaveProcessingError as e:
        logger.error(f"Leave processing error: {e}")
        return {"message": str(e), "status": "error"}
    except SQLAlchemyError as e:
        logger.error(f"Database error in process_leave_application: {e}")
        db.rollback()
        return {"message": "Database error occurred while processing leave", "status": "error"}
    except Exception as e:
        logger.error(f"Unexpected error in process_leave_application: {e}")
        db.rollback()
        return {"message": "An unexpected error occurred", "status": "error"}

def decrement_monthly_leave_count(db: Session, user_id: int) -> None:
    """Decrement monthly leave count with error handling"""
    try:
        month_str = datetime.now(UTC).strftime("%Y-%m")
        record = db.query(Threshold).filter_by(user_id=user_id, month=month_str).first()
        if record and record.leave_count > 0:
            record.leave_count -= 1
            db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error decrementing monthly leave count: {e}")
        db.rollback()

def increment_leave_balance(db: Session, user_id: int, leave_type: str, days: float) -> None:
    """Increment leave balance with error handling"""
    try:
        record = db.query(LeaveBalance).filter_by(user_id=user_id, leave_type=leave_type).first()
        if record:
            record.balance += days
            db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error incrementing leave balance: {e}")
        db.rollback()

def soft_delete_leave(db: Session, user_id: int, leave_id: int) -> Dict[str, str]:
    """Soft delete leave with comprehensive error handling"""
    try:
        leave = db.query(LeaveRequest).filter_by(id=leave_id, user_id=user_id).first()
        if not leave:
            return {"message": "Leave request not found", "status": "error"}
            
        if leave.status not in ["Pending", "Approved"]:
            return {"message": "Leave cannot be deleted in current status", "status": "error"}

        leave.status = "Deleted"
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
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in soft_delete_leave: {e}")
        db.rollback()
        return {"message": "Database error occurred while deleting leave", "status": "error"}
    except Exception as e:
        logger.error(f"Unexpected error in soft_delete_leave: {e}")
        db.rollback()
        return {"message": "An unexpected error occurred", "status": "error"}

def calculate_weekly_shrinkage_with_carry_forward(db: Session, manager_id: int, year: int = None, month: int = None):
    """Calculate weekly shrinkage with carry forward - optimized version"""
    try:
        if year is None or month is None:
            current_date = datetime.now()
            year = current_date.year if year is None else year
            month = current_date.month if month is None else month

        manager = db.query(User).get(manager_id)
        if not manager:
            return {
                "monthly_target": 0,
                "cumulative_used": 0,
                "carry_forward": 0,
                "weeks": [],
                "status": "Safe",
                "note": "Manager not found"
            }

        # Get team IDs more efficiently
        if manager.role == 'manager':
            team_ids = db.query(User.team_id).filter(
                User.reports_to_id == manager.id,
                User.role == 'associate',
                User.team_id.isnot(None)
            ).distinct().all()
            team_ids = [tid[0] for tid in team_ids]
        else:
            team_ids = [manager.team_id] if manager.team_id else []

        if not team_ids:
            return {
                "monthly_target": 0,
                "cumulative_used": 0,
                "carry_forward": 0,
                "weeks": [],
                "status": "Safe",
                "note": "No teams or associates under manager"
            }

        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()

        # Generate weeks
        current = start_date
        weeks = []
        while current <= end_date:
            week_end = min(current + timedelta(days=6 - current.weekday()), end_date)
            weeks.append((current, week_end))
            current = week_end + timedelta(days=1)

        # Get all relevant data in one query
        total_associates = db.query(User).filter(
            User.team_id.in_(team_ids),
            User.role == "associate"
        ).count()

        if total_associates == 0:
            return {
                "monthly_target": 0,
                "cumulative_used": 0,
                "carry_forward": 0,
                "weeks": [],
                "status": "Safe",
                "note": "No associates found"
            }

        # Get all approved leaves for the month
        all_leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id.in_(team_ids),
            User.role == "associate",
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        ).all()

        week_results = []
        cumulative_used = 0.0
        carry_forward = 0.0
        monthly_target = WEEKLY_TARGET * len(weeks)

        for week_start, week_end in weeks:
            # Calculate leave days for this week
            leave_days = 0.0
            for leave in all_leaves:
                if leave.start_date > week_end or leave.end_date < week_start:
                    continue
                    
                if leave.is_half_day and leave.start_date == leave.end_date:
                    if week_start <= leave.start_date <= week_end:
                        leave_days += 0.5
                else:
                    overlap_start = max(leave.start_date, week_start)
                    overlap_end = min(leave.end_date, week_end)
                    if overlap_start <= overlap_end:
                        # Count only working days
                        current_date = overlap_start
                        while current_date <= overlap_end:
                            if current_date.weekday() < 5:
                                leave_days += 1.0
                            current_date += timedelta(days=1)

            working_days = sum(1 for d in range((week_end - week_start).days + 1)
                              if (week_start + timedelta(days=d)).weekday() < 5)

            shrinkage = round((leave_days / (total_associates * working_days)) * 100, 2) if working_days > 0 else 0

            unused = WEEKLY_TARGET - shrinkage if shrinkage < WEEKLY_TARGET else 0.0
            overused = shrinkage - WEEKLY_TARGET if shrinkage > WEEKLY_TARGET else 0.0
            carry_forward += unused - overused
            cumulative_used += shrinkage

            week_results.append({
                "week_range": f"{week_start.isoformat()} to {week_end.isoformat()}",
                "shrinkage": shrinkage,
                "carry_forward": round(carry_forward, 2),
                "status": "Safe" if shrinkage <= SHRINKAGE_THRESHOLD else "Over Weekly Limit"
            })

        return {
            "monthly_target": monthly_target,
            "cumulative_used": round(cumulative_used, 2),
            "carry_forward": round(carry_forward, 2),
            "weeks": week_results,
            "status": "Safe" if cumulative_used <= monthly_target else "Exceeded",
            "note": "Shrinkage calculated over working days only"
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in calculate_weekly_shrinkage_with_carry_forward: {e}")
        return {
            "monthly_target": 0,
            "cumulative_used": 0,
            "carry_forward": 0,
            "weeks": [],
            "status": "Error",
            "note": f"Database error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error in calculate_weekly_shrinkage_with_carry_forward: {e}")
        return {
            "monthly_target": 0,
            "cumulative_used": 0,
            "carry_forward": 0,
            "weeks": [],
            "status": "Error",
            "note": f"Unexpected error: {str(e)}"
        }

# FIXED: Single definition of get_next_30_day_shrinkage for associates
def get_next_30_day_shrinkage(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Get next 30 days shrinkage and availability data with error handling and optimization"""
    try:
        logger.info(f"Getting 30-day shrinkage for user_id: {user_id}")
        
        user = db.get(User, user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return []
            
        logger.info(f"User found: {user.username}, role: {user.role}, team_id: {user.team_id}")

        # For associates, use their team_id
        if not user.team_id:
            logger.warning(f"User {user_id} not assigned to any team")
            return []

        team_id = user.team_id
        today = datetime.now().date()
        total_team_members = db.query(User).filter_by(team_id=team_id, role='associate').count()
        
        if total_team_members == 0:
            logger.warning(f"No team members found for team {team_id}")
            return []

        logger.info(f"Total team members: {total_team_members}")

        end_date = today + timedelta(days=30)
        
        # Get all approved leaves for the next 30 days
        approved_leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id == team_id,
            User.role == 'associate',
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= today
        ).all()

        logger.info(f"Found {len(approved_leaves)} approved leaves")

        results = []
        for i in range(30):
            target_date = today + timedelta(days=i)
            
            # Include ALL days (weekends and weekdays) - let frontend filter
            is_weekend = target_date.weekday() >= 5
            
            # Optional leave day logic
            is_optional_day = is_optional_leave_day(db, target_date)
            
            if is_optional_day:
                results.append({
                    "date": target_date.isoformat(),
                    "day_name": target_date.strftime("%A"),
                    "shrinkage": 0.0,
                    "availability": 100.0,
                    "status": "Safe",
                    "on_leave": [],
                    "available_count": total_team_members,
                    "total_team_members": total_team_members,
                    "leave_count": 0.0,
                    "is_weekend": is_weekend,
                    "is_optional_day": True
                })
                continue

            leave_count = 0.0
            on_leave_users = []

            # Process leaves for this specific date
            for leave in approved_leaves:
                if leave.start_date <= target_date <= leave.end_date:
                    # Add to leave count
                    if leave.is_half_day:
                        leave_count += 0.5
                    else:
                        leave_count += 1.0

                    # Add user to on_leave list (avoid duplicates)
                    user_already_added = any(
                        user_info["username"] == leave.user.username 
                        for user_info in on_leave_users
                    )
                    
                    if not user_already_added:
                        on_leave_users.append({
                            "username": leave.user.username,
                            "leave_type": leave.leave_type,
                            "is_half_day": leave.is_half_day,
                            "start_date": leave.start_date.isoformat(),
                            "end_date": leave.end_date.isoformat()
                        })

            # Calculate metrics
            shrinkage = round((leave_count / total_team_members) * 100, 2) if total_team_members > 0 else 0.0
            availability = round(100 - shrinkage, 2)
            available_count = total_team_members - int(leave_count)

            # Determine status
            if shrinkage < SAFE_SHRINKAGE_THRESHOLD:
                status = "Safe"
            elif shrinkage <= SHRINKAGE_THRESHOLD:
                status = "Tight"
            else:
                status = "Overbooked"

            results.append({
                "date": target_date.isoformat(),
                "day_name": target_date.strftime("%A"),
                "shrinkage": shrinkage,
                "availability": availability,
                "status": status,
                "on_leave": on_leave_users,
                "available_count": available_count,
                "total_team_members": total_team_members,
                "leave_count": leave_count,
                "is_weekend": is_weekend,
                "is_optional_day": False
            })

        logger.info(f"Returning {len(results)} days of data")
        return results

    except SQLAlchemyError as e:
        logger.error(f"Database error in get_next_30_day_shrinkage: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_next_30_day_shrinkage: {e}")
        return []

# FIXED: Single definition of get_manager_next_30_day_shrinkage for managers
def get_manager_next_30_day_shrinkage(db: Session, manager_id: int) -> List[Dict[str, Any]]:
    """Get manager's team shrinkage for next 30 days with enhanced data"""
    try:
        logger.info(f"Getting manager 30-day shrinkage for manager_id: {manager_id}")
        
        manager = db.get(User, manager_id)
        if not manager or manager.role != 'manager':
            logger.warning(f"Manager {manager_id} not found or not a manager")
            return []

        # Get all associates reporting to this manager
        associates = db.query(User).filter_by(reports_to_id=manager_id, role='associate').all()
        if not associates:
            logger.warning(f"No associates found for manager {manager_id}")
            return []

        associate_ids = [a.id for a in associates]
        logger.info(f"Manager {manager.username} has {len(associates)} associates")

        today = datetime.now().date()
        end_date = today + timedelta(days=30)

        # Get all approved leaves for these associates in the next 30 days
        approved_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id.in_(associate_ids),
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= today
        ).all()

        logger.info(f"Found {len(approved_leaves)} approved leaves for manager's team")

        results = []
        total_team_members = len(associates)
        
        for i in range(30):
            target_date = today + timedelta(days=i)
            
            # Include ALL days (weekends and weekdays)
            is_weekend = target_date.weekday() >= 5
            is_optional_day = is_optional_leave_day(db, target_date)

            leave_count = 0.0
            on_leave_users = []
            
            # Process leaves for this date
            for leave in approved_leaves:
                if leave.start_date <= target_date <= leave.end_date:
                    # Add to leave count
                    if leave.is_half_day:
                        leave_count += 0.5
                    else:
                        leave_count += 1.0
                    
                    # Add user to on_leave list (avoid duplicates)
                    user_already_added = any(
                        user_info["username"] == leave.user.username 
                        for user_info in on_leave_users
                    )
                    
                    if not user_already_added:
                        on_leave_users.append({
                            "username": leave.user.username,
                            "leave_type": leave.leave_type,
                            "is_half_day": leave.is_half_day,
                            "start_date": leave.start_date.isoformat(),
                            "end_date": leave.end_date.isoformat()
                        })

            # Calculate metrics
            shrinkage = round((leave_count / total_team_members) * 100, 2) if total_team_members else 0.0
            availability = round(100 - shrinkage, 2)
            available_count = total_team_members - int(leave_count)

            # Determine status
            if shrinkage < SAFE_SHRINKAGE_THRESHOLD:
                status = "Safe"
            elif shrinkage <= SHRINKAGE_THRESHOLD:
                status = "Tight"
            else:
                status = "Overbooked"

            results.append({
                "date": target_date.isoformat(),
                "day_name": target_date.strftime("%A"),
                "shrinkage": shrinkage,
                "availability": availability,
                "status": status,
                "on_leave": on_leave_users,
                "available_count": available_count,
                "total_team_members": total_team_members,
                "leave_count": leave_count,
                "is_weekend": is_weekend,
                "is_optional_day": is_optional_day
            })

        logger.info(f"Returning {len(results)} days of data for manager")
        return results

    except SQLAlchemyError as e:
        logger.error(f"Database error in get_manager_next_30_day_shrinkage: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_manager_next_30_day_shrinkage: {e}")
        return []

def get_team_availability_summary(db: Session, team_id: int, days: int = 30) -> Dict[str, Any]:
    """Get a comprehensive availability summary for a team"""
    try:
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        
        # Get total team members
        total_members = db.query(User).filter_by(team_id=team_id, role='associate').count()
        if total_members == 0:
            return {"error": "No team members found"}

        # Get all leaves for the period
        approved_leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id == team_id,
            User.role == 'associate',
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= today
        ).all()

        # Calculate daily availability
        daily_data = []
        total_working_days = 0
        critical_days = 0
        safe_days = 0
        
        for i in range(days):
            target_date = today + timedelta(days=i)
            
            # Skip weekends
            if target_date.weekday() >= 5:
                continue
                
            total_working_days += 1
            
            # Count leaves for this day
            leave_count = 0.0
            for leave in approved_leaves:
                if leave.start_date <= target_date <= leave.end_date:
                    leave_count += 0.5 if leave.is_half_day else 1.0
            
            shrinkage = (leave_count / total_members) * 100
            availability = 100 - shrinkage
            
            if shrinkage > SHRINKAGE_THRESHOLD:
                critical_days += 1
            elif shrinkage < SAFE_SHRINKAGE_THRESHOLD:
                safe_days += 1
            
            daily_data.append({
                "date": target_date.isoformat(),
                "availability": round(availability, 2),
                "people_on_leave": int(leave_count),
                "available_people": total_members - int(leave_count)
            })

        return {
            "team_id": team_id,
            "total_members": total_members,
            "period_days": total_working_days,
            "critical_days": critical_days,
            "safe_days": safe_days,
            "tight_days": total_working_days - critical_days - safe_days,
            "average_availability": round(
                sum(day["availability"] for day in daily_data) / len(daily_data), 2
            ) if daily_data else 0,
            "daily_breakdown": daily_data
        }

    except Exception as e:
        logger.error(f"Error in get_team_availability_summary: {e}")
        return {"error": str(e)}

def get_user_leave_history(db: Session, user_id: int, year: int = None) -> List[Dict[str, Any]]:
    """Get user's leave history with error handling"""
    try:
        if year is None:
            year = datetime.now().year
            
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        
        leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.start_date >= start_date,
            LeaveRequest.end_date <= end_date
        ).order_by(LeaveRequest.start_date.desc()).all()
        
        history = []
        for leave in leaves:
            leave_days = 0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
            history.append({
                "id": leave.id,
                "leave_type": leave.leave_type,
                "start_date": leave.start_date.isoformat(),
                "end_date": leave.end_date.isoformat(),
                "days": leave_days,
                "status": leave.status,
                "backup_person": leave.backup_person,
                "is_half_day": leave.is_half_day,
                "applied_on": leave.applied_on.isoformat() if leave.applied_on else None
            })
            
        return history
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_user_leave_history: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_user_leave_history: {e}")
        return []

def get_team_leave_calendar(db: Session, team_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
    """Get team leave calendar for a date range"""
    try:
        team_members = db.query(User).filter_by(team_id=team_id, role='associate').all()
        if not team_members:
            return {"calendar": [], "team_size": 0}
            
        leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id == team_id,
            User.role == 'associate',
            LeaveRequest.status.in_(['Approved', 'Pending']),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        ).all()
        
        calendar = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Only working days
                day_leaves = []
                for leave in leaves:
                    if leave.start_date <= current_date <= leave.end_date:
                        day_leaves.append({
                            "username": leave.user.username,
                            "leave_type": leave.leave_type,
                            "status": leave.status,
                            "is_half_day": leave.is_half_day
                        })
                
                shrinkage = get_team_shrinkage(db, team_id, current_date)
                
                calendar.append({
                    "date": current_date.isoformat(),
                    "shrinkage": shrinkage,
                    "status": (
                        "Safe" if shrinkage['total_shrinkage'] < SAFE_SHRINKAGE_THRESHOLD
                        else "Tight" if shrinkage['total_shrinkage'] <= SHRINKAGE_THRESHOLD
                        else "Overbooked"
                    ),
                    "leaves": day_leaves
                })
                
            current_date += timedelta(days=1)
            
        return {
            "calendar": calendar,
            "team_size": len(team_members)
        }
        
    except Exception as e:
        logger.error(f"Error in get_team_leave_calendar: {e}")
        return {"calendar": [], "team_size": 0, "error": str(e)}

def get_leave_analytics(db: Session, team_id: int, year: int = None) -> Dict[str, Any]:
    """Get comprehensive leave analytics for a team"""
    try:
        if year is None:
            year = datetime.now().year

        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()

        # Get team size
        team_size = db.query(User).filter_by(team_id=team_id, role='associate').count()
        if team_size == 0:
            return {"error": "No team members found"}

        # Get all leaves for the year (include any overlap)
        leaves = db.query(LeaveRequest).join(User).filter(
            User.team_id == team_id,
            User.role == 'associate',
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
            LeaveRequest.status == 'Approved'
        ).all()

        # Calculate analytics
        total_leave_days = sum(
            0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
            for leave in leaves
        )

        leave_by_type = {}
        leave_by_month = {i: 0 for i in range(1, 13)}

        for leave in leaves:
            # Count by type (normalize to uppercase)
            leave_type = leave.leave_type.upper()
            days = 0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
            leave_by_type[leave_type] = leave_by_type.get(leave_type, 0) + days

            # Count by month (use leave.start_date month)
            month = leave.start_date.month
            leave_by_month[month] += days

        # Calculate monthly shrinkage
        monthly_shrinkage = {}
        for month in range(1, 13):
            shrinkage = get_monthly_shrinkage(db, team_id, year, month)
            monthly_shrinkage[month] = shrinkage

        return {
            "team_size": team_size,
            "total_leave_days": total_leave_days,
            "average_leaves_per_person": round(total_leave_days / team_size, 2) if team_size else 0,
            "leave_by_type": leave_by_type,
            "leave_by_month": leave_by_month,
            "monthly_shrinkage": monthly_shrinkage,
            "year": year
        }

    except Exception as e:
        logger.error(f"Error in get_leave_analytics: {e}")
        return {"error": str(e)}

def validate_leave_request_modification(db: Session, leave_id: int, user_id: int, 
                                      new_start_date: date = None, new_end_date: date = None) -> Dict[str, Any]:
    """Validate if a leave request can be modified"""
    try:
        leave = db.query(LeaveRequest).filter_by(id=leave_id, user_id=user_id).first()
        if not leave:
            return {"valid": False, "message": "Leave request not found"}
            
        if leave.status not in ["Pending", "Approved"]:
            return {"valid": False, "message": "Leave cannot be modified in current status"}
            
        # Check if leave has already started
        today = datetime.now().date()
        if leave.start_date <= today:
            return {"valid": False, "message": "Cannot modify leave that has already started"}
            
        # If new dates provided, validate them
        if new_start_date and new_end_date:
            if new_start_date > new_end_date:
                return {"valid": False, "message": "Start date cannot be after end date"}
                
            if new_start_date < today:
                return {"valid": False, "message": "Cannot modify to past dates"}
                
            # Check for overlaps with other leaves (excluding current leave)
            overlapping_leaves = db.query(LeaveRequest).filter(
                LeaveRequest.user_id == user_id,
                LeaveRequest.id != leave_id,
                LeaveRequest.status.in_(["Pending", "Approved"]),
                or_(
                    and_(LeaveRequest.start_date <= new_start_date, LeaveRequest.end_date >= new_start_date),
                    and_(LeaveRequest.start_date <= new_end_date, LeaveRequest.end_date >= new_end_date),
                    and_(LeaveRequest.start_date >= new_start_date, LeaveRequest.end_date <= new_end_date)
                )
            ).first()
            
            if overlapping_leaves:
                return {"valid": False, "message": "New dates overlap with existing leave request"}
                
        return {"valid": True, "message": "Leave can be modified"}
        
    except Exception as e:
        logger.error(f"Error validating leave modification: {e}")
        return {"valid": False, "message": "Error validating leave request"}

def get_user_monthly_leave_summary(db: Session, user_id: int, month: str = None, year: int = None) -> Dict[str, Any]:
    """Get user's monthly leave summary with error handling"""
    try:
        from calendar import month_name
        
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return {}

        if not year:
            year = datetime.now().year

        # Determine month number if provided
        month_num = None
        if month and month != "All":
            try:
                month_num = list(month_name).index(month)
            except ValueError:
                month_num = None

        # Build query for leaves
        query = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date >= date(year, 1, 1),
            LeaveRequest.end_date <= date(year, 12, 31)
        )
        
        if month_num:
            # Get the first and last day of the month
            start = date(year, month_num, 1)
            if month_num == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month_num + 1, 1) - timedelta(days=1)
            query = query.filter(
                LeaveRequest.start_date <= end,
                LeaveRequest.end_date >= start
            )

        leaves = query.all()
        monthly_summary = {}
        leave_dates = []
        frequent_days = {}

        for leave in leaves:
            leave_type = leave.leave_type.upper()
            # Count number of requests, not days
            monthly_summary[leave_type] = monthly_summary.get(leave_type, 0) + 1

            # Collect leave dates and frequent days
            current = leave.start_date
            while current <= leave.end_date:
                leave_dates.append(current.isoformat())
                weekday = current.strftime("%A")
                frequent_days[weekday] = frequent_days.get(weekday, 0) + 1
                current += timedelta(days=1)

        return {
            "username": user.username,
            "monthly_summary": monthly_summary,
            "frequent_days": frequent_days,
            "leave_dates": leave_dates
        }
    except Exception as e:
        logger.error(f"Error in get_user_monthly_leave_summary: {e}")
        return {}

def get_pending_approvals(db: Session, manager_id: int) -> List[Dict[str, Any]]:
    """Get all pending leave requests for a manager's approval"""
    try:
        manager = db.get(User, manager_id)
        if not manager:
            return []
            
        # Get all users reporting to this manager
        if manager.role == 'manager':
            subordinates = db.query(User).filter_by(reports_to_id=manager_id).all()
            user_ids = [sub.id for sub in subordinates]
        else:
            # If not a manager, return empty list
            return []
            
        if not user_ids:
            return []
            
        pending_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id.in_(user_ids),
            LeaveRequest.status == 'Pending'
        ).order_by(LeaveRequest.applied_on.asc()).all()
        
        approvals = []
        for leave in pending_leaves:
            leave_days = 0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
            approvals.append({
                "leave_id": leave.id,
                "username": leave.user.username,
                "associate": getattr(leave.user, "full_name", leave.user.username),
                "leave_type": leave.leave_type,
                "start_date": leave.start_date.isoformat(),
                "end_date": leave.end_date.isoformat(),
                "days": leave_days,
                "backup_person": leave.backup_person,
                "is_half_day": leave.is_half_day,
                "applied_on": leave.applied_on.isoformat() if leave.applied_on else None,
                "team_id": leave.user.team_id
            })
            
        return approvals
        
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        return []

def approve_reject_leave(db: Session, leave_id: int, manager_id: int, action: str, 
                        comments: str = "") -> Dict[str, Any]:
    """Approve or reject a leave request"""
    try:
        if action not in ["Approved", "Rejected"]:
            return {"message": "Invalid action. Must be 'Approved' or 'Rejected'", "status": "error"}
            
        leave = db.get(LeaveRequest, leave_id)
        if not leave:
            return {"message": "Leave request not found", "status": "error"}
            
        if leave.status != "Pending":
            return {"message": "Leave request is not pending approval", "status": "error"}
            
        # Verify manager has authority
        manager = db.get(User, manager_id)
        if not manager or manager.role != 'manager':
            return {"message": "Invalid manager or insufficient permissions", "status": "error"}
            
        # Check if the user reports to this manager
        if leave.user.reports_to_id != manager_id:
            return {"message": "You don't have authority to approve this leave", "status": "error"}
            
        # Update leave status
        leave.status = action
        
        # If approved, update balances and counts
        if action == "Approved":
            leave_days = 0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
            increment_monthly_leave(db, leave.user_id)
            decrement_leave_balance(db, leave.user_id, leave.leave_type, leave_days)
            
        # Add log entry
        db.add(LeaveLog(
            leave_request_id=leave.id,
            changed_by=manager.username,
            action=action,
            comments=comments or f"Leave {action.lower()} by manager"
        ))
        
        db.commit()
        
        # Send notification email
        try:
            send_leave_email(
                to_email=f"{leave.user.username}{EMAIL_DOMAIN}",
                associate_name=leave.user.username,
                leave_type=leave.leave_type,
                start_date=leave.start_date,
                end_date=leave.end_date,
                status=action,
                backup_name=leave.backup_person
            )
        except Exception as e:
            logger.error(f"Error sending notification email: {e}")
            
        return {
            "message": f"Leave {action.lower()} successfully",
            "status": "success",
            "leave_id": leave_id
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in approve_reject_leave: {e}")
        db.rollback()
        return {"message": "Database error occurred", "status": "error"}
    except Exception as e:
        logger.error(f"Unexpected error in approve_reject_leave: {e}")
        db.rollback()
        return {"message": "An unexpected error occurred", "status": "error"}

def get_leave_balance_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Get comprehensive leave balance summary for a user"""
    try:
        user = db.get(User, user_id)
        if not user:
            return {"error": "User not found"}
            
        # Get all leave types and their balances
        balances = db.query(LeaveBalance).filter_by(user_id=user_id).all()
        balance_dict = {balance.leave_type: balance.balance for balance in balances}
        
        # Get current month's leave count
        current_month_count = get_monthly_leave_count(db, user_id)
        
        # Get used leaves this year
        year = datetime.now().year
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        
        used_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == 'Approved',
            LeaveRequest.start_date >= start_date,
            LeaveRequest.end_date <= end_date
        ).all()
        
        used_by_type = {}
        for leave in used_leaves:
            leave_type = leave.leave_type
            days = 0.5 if leave.is_half_day else (leave.end_date - leave.start_date).days + 1
            used_by_type[leave_type] = used_by_type.get(leave_type, 0) + days
            
        return {
            "user_id": user_id,
            "username": user.username,
            "available_balances": balance_dict,
            "used_this_year": used_by_type,
            "leave_type_summary": used_by_type,  # For frontend compatibility
            "current_month_leave_count": current_month_count,
            "monthly_limit": MONTHLY_LEAVE_LIMIT,
            "remaining_monthly_quota": max(0, MONTHLY_LEAVE_LIMIT - current_month_count)
        }
        
    except Exception as e:
        logger.error(f"Error in get_leave_balance_summary: {e}")
        return {"error": str(e)}