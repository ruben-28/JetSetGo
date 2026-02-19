"""
Module de Sécurité
Gestion du hachage des mots de passe et de la génération de tokens JWT.
"""

from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
import os
import warnings

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SECURITE: Charger le secret JWT depuis les variables d'environnement
# Générer un secret sécurisé: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h par défaut

# Avertir si le secret par défaut est utilisé
if JWT_SECRET == "CHANGE_ME_SUPER_SECRET":
    warnings.warn(
        "⚠️  Utilisation du JWT_SECRET par défaut ! Définissez la variable d'environnement JWT_SECRET en production.",
        RuntimeWarning
    )


def _bcrypt_ok(password: str) -> bool:
    """Vérifie si le mot de passe est compatible avec bcrypt (max 72 octets)."""
    # bcrypt limite en BYTES (UTF-8)
    return len(password.encode("utf-8")) <= 72


def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt."""
    if not _bcrypt_ok(password):
        raise ValueError("Mot de passe trop long (max 72 octets).")
    return PWD_CONTEXT.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    if not _bcrypt_ok(password):
        return False
    return PWD_CONTEXT.verify(password, password_hash)


def create_access_token(payload: dict) -> str:
    """Crée un token d'accès JWT."""
    exp = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = dict(payload)
    to_encode.update({"exp": exp})  # Expiration du token
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
