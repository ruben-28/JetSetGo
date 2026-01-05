from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import User
from .security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# --------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------- Schemas ----------
class RegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    username_or_email: str
    password: str

class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

# --------- Helpers ----------
def find_user_by_username_or_email(db: Session, s: str):
    return db.query(User).filter(
        (User.username == s) | (User.email == s)
    ).first()

# --------- Endpoints ----------
@router.post("/register", response_model=AuthOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username déjà utilisé")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.username)
    return AuthOut(access_token=token, user_id=user.id, username=user.username)

@router.post("/login", response_model=AuthOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = find_user_by_username_or_email(db, data.username_or_email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")


    token = create_access_token(user.id, user.username)
    return AuthOut(access_token=token, user_id=user.id, username=user.username)
