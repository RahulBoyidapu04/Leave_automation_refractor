from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import logging
from app.database import get_db
from app.auth import get_current_user
from app.models import Notification, User, LeaveRequest

# Import the updated logic functions (FIXED - removed duplicate import)
from app.logic import (
    # Core leave processing
    process_leave_application,
    get_manager_next_30_day_shrinkage,
    get_user_monthly_leave_summary,
    get_next_30_day_shrinkage,
    soft_delete_leave,
    
    # Shrinkage calculations
    get_dashboard_shrinkage,
    get_monthly_shrinkage,
    calculate_weekly_shrinkage_with_carry_forward,
    get_manager_dashboard_shrinkage,
    get_team_availability_summary,
    get_team_shrinkage,
    
    # Enhanced functions
    get_user_leave_history,
    get_team_leave_calendar,
    get_leave_analytics,
    validate_leave_request_modification,
    get_pending_approvals,
    approve_reject_leave,
    get_leave_balance_summary,
    
    # Exception classes
    ValidationError,
    LeaveProcessingError,
    
    # Utility functions
    parse_safe_date
)

# Configure router and logger
router = APIRouter(prefix="/api/v1/leave", tags=["Leave Management"])
logger = logging.getLogger(__name__)

# ==================== PYDANTIC MODELS ====================

class LeaveApplicationRequest(BaseModel):
    """Request model for leave application"""
    leave_type: str = Field(..., min_length=1, max_length=50, description="Type of leave (AL, CL, SL, Optional, Sick)")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    backup_person: Optional[str] = Field(None, max_length=100, description="Name of backup person")
    is_half_day: bool = Field(False, description="Whether this is a half-day leave")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for leave")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if not v:
            raise ValueError('Date cannot be empty')
        try:
            parsed_date = datetime.strptime(v, '%Y-%m-%d')
            if parsed_date.date() < datetime.now().date():
                raise ValueError('Date cannot be in the past')
            return v
        except ValueError as e:
            if "past" in str(e):
                raise e
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('leave_type')
    def validate_leave_type(cls, v):
        valid_types = ['AL', 'CL', 'SL', 'Optional', 'Sick', 'Emergency', 'Maternity', 'Paternity']
        if v.upper() not in [t.upper() for t in valid_types]:
            raise ValueError(f'Leave type must be one of: {", ".join(valid_types)}')
        return v.upper()

    class Config:
        schema_extra = {
            "example": {
                "leave_type": "AL",
                "start_date": "2024-12-25",
                "end_date": "2024-12-26",
                "backup_person": "John Doe",
                "is_half_day": False,
                "reason": "Family vacation"
            }
        }

class LeaveApprovalRequest(BaseModel):
    """Request model for leave approval/rejection"""
    action: str = Field(..., description="Action to take: 'Approved' or 'Rejected'")
    comments: Optional[str] = Field("", max_length=1000, description="Comments for the approval/rejection")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['Approved', 'Rejected']:
            raise ValueError('Action must be either "Approved" or "Rejected"')
        return v

    class Config:
        schema_extra = {
            "example": {
                "action": "Approved",
                "comments": "Leave approved as per policy"
            }
        }

class LeaveModificationRequest(BaseModel):
    """Request model for leave modification"""
    new_start_date: Optional[str] = Field(None, description="New start date in YYYY-MM-DD format")
    new_end_date: Optional[str] = Field(None, description="New end date in YYYY-MM-DD format")
    new_backup_person: Optional[str] = Field(None, max_length=100, description="New backup person")
    new_reason: Optional[str] = Field(None, max_length=500, description="New reason for leave")
    
    @validator('new_start_date', 'new_end_date')
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

class StandardResponse(BaseModel):
    """Standard API response model"""
    message: str
    status: str
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "status": "success",
                "data": {},
                "timestamp": "2024-01-01T12:00:00"
            }
        }

# ==================== UTILITY FUNCTIONS ====================

def handle_api_error(error: Exception, default_message: str = "An error occurred") -> HTTPException:
    """Standardized error handling"""
    if isinstance(error, ValidationError):
        logger.warning(f"Validation error: {error}")
        return HTTPException(status_code=400, detail=str(error))
    elif isinstance(error, LeaveProcessingError):
        logger.error(f"Processing error: {error}")
        return HTTPException(status_code=422, detail=str(error))
    elif isinstance(error, HTTPException):
        return error
    else:
        logger.error(f"Unexpected error: {error}")
        return HTTPException(status_code=500, detail=default_message)

def validate_team_access(current_user: User) -> int:
    """Validate user has team access and return team_id"""
    team_id = current_user.team_id
    if not team_id:
        raise HTTPException(status_code=400, detail="User not assigned to any team")
    return team_id

def validate_manager_access(current_user: User) -> int:
    """Validate user is a manager and return user_id"""
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can access this resource")
    return current_user.id

# ==================== CORE LEAVE ROUTES ====================

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.post("/apply", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_leave(
    request: LeaveApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply for leave with comprehensive validation and processing"""
    try:
        start_date = parse_safe_date(request.start_date)
        end_date = parse_safe_date(request.end_date)
        if start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
        
        leave_data = {
            "user_id": current_user.id,
            "leave_type": request.leave_type,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "backup_person": request.backup_person,
            "is_half_day": request.is_half_day,
            "reason": request.reason
        }
        
        result = process_leave_application(db, leave_data)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return StandardResponse(
            message=result["message"],
            status="success",
            data={
                "leave_id": result.get("leave_id"),
                "leave_type": request.leave_type,
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to process leave application")

@router.delete("/cancel/{leave_id}", response_model=StandardResponse)
async def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel/delete a leave request"""
    try:
        if leave_id <= 0:
            raise ValidationError("Invalid leave ID")
        
        result = soft_delete_leave(db, current_user.id, leave_id)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return StandardResponse(
            message=result["message"],
            status="success",
            data={"leave_id": leave_id}
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to cancel leave")

@router.get("/history", response_model=StandardResponse)
async def get_leave_history(
    year: Optional[int] = Query(None, description="Year (defaults to current year)", ge=2020, le=2030),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's leave history for a specific year"""
    try:
        if year and (year < 2020 or year > 2030):
            raise ValidationError("Year must be between 2020 and 2030")
        
        history = get_user_leave_history(db, current_user.id, year)
        
        return StandardResponse(
            message="Leave history retrieved successfully",
            status="success",
            data={
                "history": history,
                "year": year or datetime.now().year,
                "total_requests": len(history)
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get leave history")

@router.get("/balance", response_model=StandardResponse)
async def get_balance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's comprehensive leave balance summary"""
    try:
        balance_summary = get_leave_balance_summary(db, current_user.id)
        if "error" in balance_summary:
            raise HTTPException(status_code=400, detail=balance_summary["error"])
        
        return StandardResponse(
            message="Balance summary retrieved successfully",
            status="success",
            data=balance_summary
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get balance summary")

@router.get("/validate-modification/{leave_id}", response_model=StandardResponse)
async def validate_modification(
    leave_id: int,
    new_start_date: Optional[str] = Query(None, description="New start date in YYYY-MM-DD format"),
    new_end_date: Optional[str] = Query(None, description="New end date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate if a leave request can be modified"""
    try:
        if leave_id <= 0:
            raise ValidationError("Invalid leave ID")
        
        new_start = parse_safe_date(new_start_date) if new_start_date else None
        new_end = parse_safe_date(new_end_date) if new_end_date else None
        
        if new_start and new_end and new_start > new_end:
            raise ValidationError("New start date cannot be after new end date")
        
        validation_result = validate_leave_request_modification(
            db, leave_id, current_user.id, new_start, new_end
        )
        
        return StandardResponse(
            message="Validation completed",
            status="success",
            data=validation_result
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to validate modification")

# ==================== TEAM & SHRINKAGE ROUTES ====================

@router.get("/dashboard/shrinkage", response_model=StandardResponse)
async def get_team_dashboard_shrinkage(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to today)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team or manager shrinkage data for dashboard display"""
    try:
        target_date = parse_safe_date(date) if date else None

        if current_user.role == "manager":
            shrinkage_data = get_manager_dashboard_shrinkage(db, current_user.id, target_date)
            team_id = None  # Manager may have multiple teams
        else:
            team_id = validate_team_access(current_user)
            shrinkage_data = get_dashboard_shrinkage(db, team_id, target_date)

        return StandardResponse(
            message="Shrinkage data retrieved successfully",
            status="success",
            data={
                **shrinkage_data,
                "team_id": team_id
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get shrinkage data")

@router.get("/dashboard/on-leave-today", response_model=StandardResponse)
async def get_associates_on_leave_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return associates on leave today for the manager."""
    today = datetime.now().date()
    if current_user.role != "manager":
        return StandardResponse(message="Not authorized", status="error", data=[])
    
    # Get associates reporting to this manager
    associates = db.query(User).filter_by(reports_to_id=current_user.id, role='associate').all()
    associate_ids = [a.id for a in associates]
    
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id.in_(associate_ids),
        LeaveRequest.status == "Approved",
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).all()
    
    data = [
        {
            "username": leave.user.username,
            "leave_type": leave.leave_type,
            "is_half_day": leave.is_half_day
        }
        for leave in leaves
    ]
    return StandardResponse(message="Associates on leave today", status="success", data=data)

@router.get("/shrinkage/monthly", response_model=StandardResponse)
async def get_team_monthly_shrinkage(
    year: int = Query(..., description="Year", ge=2020, le=2030),
    month: int = Query(..., description="Month (1-12)", ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly shrinkage percentage for team"""
    try:
        team_id = validate_team_access(current_user)
        shrinkage = get_monthly_shrinkage(db, team_id, year, month)
        
        return StandardResponse(
            message="Monthly shrinkage retrieved successfully",
            status="success",
            data={
                "year": year,
                "month": month,
                "shrinkage": shrinkage,
                "team_id": team_id,
                "status": "Safe" if shrinkage < 6 else "Tight" if shrinkage <= 10 else "Overbooked"
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get monthly shrinkage")

@router.get("/shrinkage/next30days")
async def get_next_30_days_shrinkage(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get next 30 days shrinkage data for a specific user"""
    user = db.get(User, user_id)
    if user and user.role == "manager":
        return get_manager_next_30_day_shrinkage(db, user_id)
    else:
        return get_next_30_day_shrinkage(db, user_id)

@router.get("/forecast/l5-30days")
async def l5_next_30_days(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get L5 availability forecast (L5 role only)"""
    if current_user.role != "l5":
        raise HTTPException(status_code=403, detail="Only L5s allowed")
    # You can call the same logic as in admin_routes.py
    try:
        from app.admin_routes import get_l5_availability
        return get_l5_availability(db, current_user)
    except ImportError:
        raise HTTPException(status_code=501, detail="L5 availability not implemented")

# UPDATED: Fixed 30-day forecast route to match enhanced logic
@router.get("/forecast/30days", response_model=StandardResponse)
async def get_30_day_forecast(
    user_id: Optional[int] = Query(None, description="Associate user ID (for managers)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get next 30 days leave forecast with shrinkage analysis"""
    try:
        logger.info(f"Getting 30-day forecast for user: {current_user.username}, role: {current_user.role}")
        
        # Determine which user's data to fetch
        target_user_id = current_user.id
        
        # If manager and user_id is provided, show for that associate
        if current_user.role == "manager" and user_id:
            # Verify the user_id belongs to an associate under this manager
            associate = db.query(User).filter(
                User.id == user_id,
                User.reports_to_id == current_user.id,
                User.role == 'associate'
            ).first()
            
            if not associate:
                raise HTTPException(
                    status_code=403, 
                    detail="You can only view data for associates reporting to you"
                )
            target_user_id = user_id
            
        elif current_user.role == "manager":
            # Manager viewing their own team data
            target_user_id = current_user.id
        
        # Get the forecast data using the enhanced functions
        if current_user.role == "manager":
            forecast_data = get_manager_next_30_day_shrinkage(db, target_user_id)
        else:
            forecast_data = get_next_30_day_shrinkage(db, target_user_id)

        logger.info(f"Retrieved {len(forecast_data)} days of forecast data")

        # FIXED: Create default data that includes ALL 30 days (including weekends)
        if not forecast_data:
            logger.warning("No forecast data returned, creating default data")
            today = datetime.now().date()
            forecast_data = []
            for i in range(30):
                target_date = today + timedelta(days=i)
                forecast_data.append({
                    "date": target_date.isoformat(),
                    "day_name": target_date.strftime("%A"),
                    "shrinkage": 0,
                    "availability": 100,
                    "status": "Safe",
                    "on_leave": [],
                    "available_count": 0,
                    "total_team_members": 0,
                    "leave_count": 0,
                    "is_weekend": target_date.weekday() >= 5,
                    "is_optional_day": False
                })

        # UPDATED: Calculate summary statistics correctly
        # Count working days (not weekends) for statistics
        working_days = [day for day in forecast_data if not day.get("is_weekend", False)]
        all_days = forecast_data  # Include all days for total count
        
        avg_shrinkage = sum(day.get("shrinkage", 0) for day in working_days) / len(working_days) if working_days else 0
        high_risk_days = len([day for day in working_days if day.get("shrinkage", 0) > 10])

        return StandardResponse(
            message="30-day forecast retrieved successfully",
            status="success",
            data={
                "forecast": forecast_data,  # This now includes ALL 30 days
                "summary": {
                    "total_working_days": len(working_days),
                    "total_days": len(all_days),  # Total days including weekends
                    "average_shrinkage": round(avg_shrinkage, 2),
                    "high_risk_days": high_risk_days,
                    "forecast_period": "Next 30 days",
                    "user_role": current_user.role,
                    "target_user_id": target_user_id
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_30_day_forecast: {e}")
        raise handle_api_error(e, "Failed to get forecast data")

# ==================== MANAGER-ONLY ROUTES ====================

@router.get("/shrinkage/weekly-carry-forward", response_model=StandardResponse)
async def get_weekly_shrinkage_with_carry_forward(
    year: Optional[int] = Query(None, description="Year (defaults to current year)", ge=2020, le=2030),
    month: Optional[int] = Query(None, description="Month (defaults to current month)", ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly shrinkage with carry forward calculation (Manager only)"""
    try:
        manager_id = validate_manager_access(current_user)
        result = calculate_weekly_shrinkage_with_carry_forward(db, manager_id, year, month)
        
        return StandardResponse(
            message="Weekly shrinkage with carry forward retrieved successfully",
            status="success",
            data=result
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get weekly shrinkage data")

@router.get("/team/availability-summary", response_model=StandardResponse)
async def team_availability_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a comprehensive availability summary for the current user's team."""
    try:
        team_id = validate_team_access(current_user)
        summary = get_team_availability_summary(db, team_id, days)
        if "error" in summary:
            raise HTTPException(status_code=400, detail=summary["error"])
        return StandardResponse(
            message="Team availability summary retrieved successfully",
            status="success",
            data=summary
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get team availability summary")

@router.get("/pending-approvals", response_model=StandardResponse)
async def get_pending_leave_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending leave requests for manager approval (Manager only)"""
    try:
        manager_id = validate_manager_access(current_user)
        pending_approvals = get_pending_approvals(db, manager_id)
        
        # Group by priority/urgency
        urgent_leaves = [leave for leave in pending_approvals 
                        if datetime.strptime(leave["start_date"], "%Y-%m-%d").date() <= 
                        (datetime.now().date() + timedelta(days=7))]
        
        return StandardResponse(
            message="Pending approvals retrieved successfully",
            status="success",
            data={
                "pending_leaves": pending_approvals,
                "total_pending": len(pending_approvals),
                "urgent_approvals": len(urgent_leaves),
                "urgent_leaves": urgent_leaves
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get pending approvals")

@router.post("/approve/{leave_id}", response_model=StandardResponse)
async def approve_or_reject_leave(
    leave_id: int,
    request: LeaveApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve or reject a leave request (Manager only)"""
    try:
        manager_id = validate_manager_access(current_user)
        
        if leave_id <= 0:
            raise ValidationError("Invalid leave ID")
            
        result = approve_reject_leave(
            db, leave_id, manager_id, request.action, request.comments
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return StandardResponse(
            message=result["message"],
            status="success",
            data={
                "leave_id": result.get("leave_id"),
                "action": request.action,
                "processed_by": current_user.username
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to process leave approval")

# ==================== UTILITY ROUTES ====================

@router.get("/health", response_model=StandardResponse)
async def health_check():
    """Health check endpoint for service monitoring"""
    return StandardResponse(
        message="Leave management service is healthy",
        status="success",
        data={
            "service": "leave-management",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "uptime": "Service is operational"
        }
    )

@router.get("/team/members", response_model=StandardResponse)
async def get_team_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of team members (for backup person selection, etc.)"""
    try:
        if current_user.role == "manager":
            # Managers: all associates who report to them
            team_members = db.query(User).filter(
                User.reports_to_id == current_user.id,
                User.role == 'associate'
            ).all()
            team_id = None  # Managers may have multiple teams
        else:
            # Team leads: all associates in their team (excluding self)
            team_id = validate_team_access(current_user)
            team_members = db.query(User).filter(
                User.team_id == team_id,
                User.role == 'associate',
                User.id != current_user.id
            ).all()

        members_list = [
            {
                "id": member.id,
                "username": member.username,
                "full_name": getattr(member, 'full_name', member.username)
            }
            for member in team_members
        ]
        
        return StandardResponse(
            message="Team members retrieved successfully",
            status="success",
            data={
                "team_id": team_id,
                "members": members_list,
                "total_members": len(members_list)
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get team members")

@router.get("/stats/dashboard", response_model=StandardResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for user overview"""
    try:
        user_id = current_user.id
        
        # Get user's current balances
        balance_summary = get_leave_balance_summary(db, user_id)
        
        # Get pending requests
        pending_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == 'Pending'
        ).count()
        
        # Get upcoming leaves
        upcoming_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == 'Approved',
            LeaveRequest.start_date >= datetime.now().date()
        ).count()
        
        # Get team shrinkage if user has team
        team_shrinkage = None
        if current_user.team_id:
            shrinkage_data = get_dashboard_shrinkage(db, current_user.team_id)
            team_shrinkage = shrinkage_data
        
        return StandardResponse(
            message="Dashboard stats retrieved successfully",
            status="success",
            data={
                "user_stats": {
                    "pending_requests": pending_leaves,
                    "upcoming_leaves": upcoming_leaves,
                    "monthly_quota_used": balance_summary.get("current_month_leave_count", 0),
                    "monthly_quota_remaining": balance_summary.get("remaining_monthly_quota", 0)
                },
                "leave_balances": balance_summary.get("available_balances", {}),
                "team_shrinkage": team_shrinkage
            }
        )
    except Exception as e:
        raise handle_api_error(e, "Failed to get dashboard stats")

@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for the current user."""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return {
        "status": "success",
        "data": {
            "notifications": [
                {
                    "id": n.id,
                    "message": n.message,
                    "created_at": n.created_at,
                    "read": n.read
                } for n in notifications
            ]
        }
    }

@router.get("/analytics", response_model=StandardResponse)
async def get_team_analytics(
    user_id: Optional[int] = Query(None, description="Associate user ID (optional)"),
    month: Optional[str] = Query(None, description="Month name or 'All' (optional)"),
    year: Optional[int] = Query(None, description="Year (defaults to current year)", ge=2020, le=2030),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive leave analytics for team or associate (Manager/Team Lead only)"""
    try:
        if current_user.role not in ["manager", "team_lead"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to access analytics")
        
        if user_id:
            summary = get_user_monthly_leave_summary(db, user_id, month, year)
            return StandardResponse(
                message="Leave pattern summary retrieved successfully",
                status="success",
                data=summary
            )
        else:
            team_id = validate_team_access(current_user)
            analytics_data = get_leave_analytics(db, team_id, year)
            if "error" in analytics_data:
                raise HTTPException(status_code=400, detail=analytics_data["error"])
            return StandardResponse(
                message="Analytics retrieved successfully",
                status="success",
                data=analytics_data
            )
    except Exception as e:
        raise handle_api_error(e, "Failed to get analytics")