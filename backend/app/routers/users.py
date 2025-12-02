from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token, SECRET_KEY
from app.schemas import UserCreate, UserOut, Token
from jose import JWTError, jwt

router = APIRouter()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if username already exists (case-insensitive)
        # Use lower() for compatibility with both PostgreSQL and SQLite
        username_lower = user.username.strip().lower()
        existing_user = db.query(User).filter(
            func.lower(User.username) == username_lower
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Truncate password to 72 bytes for bcrypt compatibility
        password = user.password
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
        
        hashed = hash_password(password)
        db_user = User(username=user.username.strip(), password_hash=hashed)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Case-insensitive username lookup
        # Use lower() for compatibility with both PostgreSQL and SQLite
        username_lower = user.username.strip().lower()
        db_user = db.query(User).filter(
            func.lower(User.username) == username_lower
        ).first()
        
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password (truncate if too long for bcrypt)
        password_to_verify = user.password
        if len(password_to_verify.encode('utf-8')) > 72:
            password_to_verify = password_to_verify.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        if not verify_password(password_to_verify, db_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token({"sub": db_user.username})
        return Token(access_token=token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/", response_model=list[UserOut])
def get_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/search/{username}", response_model=list[UserOut])
def search_users(username: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    # Search users (excluding current user)
    users = db.query(User).filter(
        User.username.contains(username.strip()),
        User.id != current_user.id
    ).all()
    return users
