from sqlalchemy import (
    Column, Integer, String, Date, DateTime,
    ForeignKey, Float, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from passlib.hash import bcrypt


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    reports_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # ✅ Manager hierarchy

    # Relationships
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    manager = relationship("User", remote_side=[id])  # Self-reference for hierarchy
    leaves = relationship("LeaveRequest", back_populates="user", cascade="all, delete-orphan")
    leave_balances = relationship("LeaveBalance", backref="user", cascade="all, delete-orphan")
    thresholds = relationship("Threshold", backref="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", backref="user", cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.hashed_password = bcrypt.hash(raw_password)

    def check_password(self, raw_password):
        return bcrypt.verify(raw_password, self.hashed_password)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    manager_id = Column(Integer, ForeignKey("users.id"))
    shrinkage_limit = Column(Float, default=10.0)

    manager = relationship("User", backref="managed_teams", foreign_keys=[manager_id])
    members = relationship("User", back_populates="team", foreign_keys="User.team_id", cascade="all, delete")

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name}, manager_id={self.manager_id})>"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    leave_type = Column(String)
    status = Column(String)
    applied_on = Column(DateTime, default=datetime.utcnow)
    comments = Column(String, nullable=True)
    backup_person = Column(String, nullable=True)
    is_half_day = Column(Boolean, default=False)

    user = relationship("User", back_populates="leaves")
    logs = relationship("LeaveLog", back_populates="leave_request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LeaveRequest(id={self.id}, user_id={self.user_id}, status={self.status})>"

    def get_leave_days(self):
        """Return 0.5 if it's a half day, else total days between start and end date inclusive"""
        if not self.start_date or not self.end_date:
            return 0
        delta = (self.end_date - self.start_date).days + 1
        return 0.5 if self.is_half_day else delta


class Threshold(Base):
    __tablename__ = "thresholds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    month = Column(String)
    leave_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Threshold(user_id={self.user_id}, month={self.month}, count={self.leave_count})>"


class LeaveLog(Base):
    __tablename__ = "leave_logs"

    id = Column(Integer, primary_key=True)
    leave_request_id = Column(Integer, ForeignKey("leave_requests.id"))
    changed_by = Column(String)
    action = Column(String)
    comments = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    leave_request = relationship("LeaveRequest", back_populates="logs")

    def __repr__(self):
        return f"<LeaveLog(id={self.id}, action={self.action}, by={self.changed_by})>"


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    leave_type = Column(String)
    balance = Column(Float, default=0.0)

    def __repr__(self):
        return f"<LeaveBalance(user_id={self.user_id}, type={self.leave_type}, balance={self.balance})>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, message={self.message})>"

from sqlalchemy import Column, Integer, Date
from app.database import Base

class OptionalLeaveDate(Base):
    __tablename__ = "optional_leave_dates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)