from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date


class UserBase(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True  # Pydantic v2+


class LeaveResponse(BaseModel):
    id: int
    leave_type: str
    start_date: Optional[str]  # ISO string format
    end_date: Optional[str]    # ISO string format
    status: str
    backup_person: Optional[str] = None
    is_half_day: Optional[bool] = False

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    message: str
    read: bool
    created_at: Optional[str]

    class Config:
        from_attributes = True


class LeaveBalanceResponse(BaseModel):
    leave_type: str
    balance: float

    class Config:
        from_attributes = True


from pydantic import BaseModel
from typing import Optional

class LeaveResponse(BaseModel):
    id: int
    leave_type: str
    start_date: str  # <-- must match the actual serialized format
    end_date: str
    status: str
    backup_person: Optional[str] = None
    is_half_day: Optional[bool] = False

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat(),
        }


    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    id: int
    name: str
    manager_id: Optional[int]

    class Config:
        from_attributes = True
