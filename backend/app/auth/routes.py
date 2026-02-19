"""
Fichier: backend/app/auth/routes.py
Objectif: Définition des endpoints API pour l'authentification.
Responsabilités:
- Inscription des utilisateurs (/register).
- Connexion et génération de token (/login).
- Validation des entrées (Pydantic models).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth.db import get_db
from app.auth.models import User
from app.auth.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    """Modèle d'entrée pour l'inscription."""
    username: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    """Modèle d'entrée pour la connexion."""
    username_or_email: str
    password: str


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    """
    Endpoint d'inscription d'un nouvel utilisateur.
    Vérifie l'unicité du nom d'utilisateur et de l'email avant de créer le compte.
    """
    # Vérifie doublons (plus clair que laisser exploser SQLAlchemy)
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username déjà utilisé")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Hash password (peut lever ValueError si > 72 bytes)
    try:
        pw_hash = hash_password(data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = User(username=data.username, email=data.email, password_hash=pw_hash)
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username/Email déjà utilisé")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    """
    Endpoint de connexion.
    Vérifie les identifiants et retourne un token JWT.
    """
    # Recherche par username OU email
    user = (
        db.query(User)
        .filter((User.username == data.username_or_email) | (User.email == data.username_or_email))
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
