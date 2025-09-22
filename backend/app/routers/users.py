from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token
from app.schemas import UserCreate, UserOut, Token
from jose import JWTError, jwt

router = APIRouter()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, "supersecret", algorithms=["HS256"])
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
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hash_password(user.password)
    db_user = User(username=user.username, password_hash=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token}

@router.get("/", response_model=list[UserOut])
def get_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/search/{username}", response_model=list[UserOut])
def search_users(username: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).filter(User.username.contains(username)).all()
