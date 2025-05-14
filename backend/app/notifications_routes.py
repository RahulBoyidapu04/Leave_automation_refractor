from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from .database import get_db
from .models import User, Notification
from .auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notifications"])

# ------------------ Models ------------------
class NotificationCreate(BaseModel):
    user_id: int
    message: str

class NotificationResponse(BaseModel):
    id: int
    message: str
    read: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# ------------------ Routes ------------------
@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_notification(
    note: NotificationCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new notification (manager and L5 only)"""
    if current_user.role not in ("manager", "l5"):
        logger.warning(f"Unauthorized notification creation attempt by {current_user.username}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # Validate target user exists
    target_user = db.query(User).get(note.user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
    
    # Create notification
    new_note = Notification(
        user_id=note.user_id, 
        message=note.message, 
        read=False
    )
    
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    
    logger.info(f"Notification created by {current_user.username} for user {note.user_id}")
    return {"message": "Notification created", "id": new_note.id}

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = False, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Return a list of notifications for the current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).all()
    return notifications

@router.post("/{note_id}/read")
def mark_one_read(
    note_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    note = db.query(Notification).filter(
        Notification.id == note_id, 
        Notification.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    
    note.read = True
    db.commit()
    
    logger.info(f"User {current_user.username} marked notification {note_id} as read")
    return {"message": "Notification marked as read"}

@router.post("/mark-read")
def mark_all_read(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    updated = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).update({"read": True})
    
    db.commit()
    
    logger.info(f"User {current_user.username} marked {updated} notifications as read")
    return {"message": f"{updated} notifications marked as read"}

@router.get("/count")
def get_notification_count(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).count()
    
    return {"unread_count": count}

@router.delete("/{note_id}")
def delete_notification(
    note_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Delete a specific notification."""
    note = db.query(Notification).filter(
        Notification.id == note_id, 
        Notification.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    
    db.delete(note)
    db.commit()
    
    logger.info(f"Notification {note_id} deleted by user {current_user.username}")
    return {"message": "Notification deleted"}


@router.get("/notifications/me")
def get_my_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()

@router.post("/notifications/mark-all-read")
def mark_all_as_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter_by(user_id=current_user.id, read=False).update({"read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
