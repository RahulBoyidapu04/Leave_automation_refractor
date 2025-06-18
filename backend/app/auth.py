from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import secrets
from typing import Optional

from .models import User
from app.database import get_db
import logging

# Configure logging - but don't log sensitive data
logger = logging.getLogger(__name__)

# ------------------ Config ------------------
# In production, these should come from environment variables with no defaults
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise ValueError("SECRET_KEY environment variable must be set in production")
    else:
        SECRET_KEY = secrets.token_hex(32)  # Generate secure key for development
        
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Make sure tokenUrl matches your router prefix + route path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ------------------ Token Schema ------------------
class TokenData(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    role: Optional[str] = None
    
class RefreshToken(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: int  # Unix timestamp for token expiration

# ------------------ JWT Token Creation ------------------
def create_access_token(user: User):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user.username,
        "exp": expire,
        "role": user.role,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user: User):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user.username,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_tokens(user: User):
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    expires_at = int((datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

# ------------------ Auth Dependency ------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")
        
        if username is None or token_type != "access":
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logger.warning(f"User not found: {username}")
        raise credentials_exception
        
    return user

# ------------------ Role-Based Access Control ------------------
def get_manager_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# ------------------ Auth Router ------------------
router = APIRouter(tags=["Auth"])

# Rate limiting variables
login_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 15 * 60  # 15 minutes in seconds

def check_rate_limit(username: str, ip: str):
    """Check if a user or IP has exceeded login attempt limits"""
    current_time = datetime.utcnow().timestamp()
    key = f"{username}:{ip}"
    
    if key in login_attempts:
        attempts, locked_until = login_attempts[key]
        
        # Check if user is in lockout period
        if locked_until and current_time < locked_until:
            remaining = int(locked_until - current_time)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {remaining} seconds."
            )
            
        # Reset attempts if lockout has expired
        if locked_until and current_time >= locked_until:
            login_attempts[key] = (0, None)
            
    else:
        login_attempts[key] = (0, None)

@router.post("/auth/token", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Authenticate user and return access & refresh tokens"""
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Check rate limiting before processing
        check_rate_limit(form_data.username, client_ip)
        
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not user.check_password(form_data.password):
            # Increment failed attempts
            key = f"{form_data.username}:{client_ip}"
            attempts, _ = login_attempts.get(key, (0, None))
            attempts += 1
            
            # If max attempts reached, lock the account
            if attempts >= MAX_ATTEMPTS:
                lockout_until = datetime.utcnow().timestamp() + LOCKOUT_TIME
                login_attempts[key] = (attempts, lockout_until)
                logger.warning(f"Account locked due to failed attempts: {form_data.username} from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts. Try again in {LOCKOUT_TIME} seconds."
                )
            else:
                login_attempts[key] = (attempts, None)
                
            # Return generic error for security
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
            
        # Reset failed attempts on successful login
        key = f"{form_data.username}:{client_ip}"
        if key in login_attempts:
            login_attempts[key] = (0, None)
            
        logger.info(f"User logged in: {user.username}")
        return create_tokens(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

@router.post("/auth/refresh", response_model=Token)
def refresh_token(token_data: RefreshToken, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise credentials_exception
            
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
            
        return create_tokens(user)
        
    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint - for client-side token removal"""
    # Note: JWT tokens can't be invalidated server-side without additional
    # infrastructure like a token blacklist/database
    return {"message": "Successfully logged out"}

# Debug route - should be disabled in production
if os.getenv("ENVIRONMENT", "development") != "production":
    @router.get("/auth/test")
    def test_auth_route(current_user: User = Depends(get_current_user)):
        return {
            "message": "Auth router is working",
            "user": current_user.username,
            "role": current_user.role
        }