from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = "CHANGE_ME_SUPER_SECRET"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24


def _bcrypt_ok(password: str) -> bool:
    # bcrypt limite en BYTES (UTF-8)
    return len(password.encode("utf-8")) <= 72


def hash_password(password: str) -> str:
    if not _bcrypt_ok(password):
        raise ValueError("Mot de passe trop long (max 72 bytes).")
    return PWD_CONTEXT.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not _bcrypt_ok(password):
        return False
    return PWD_CONTEXT.verify(password, password_hash)


def create_access_token(payload: dict) -> str:
    exp = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = dict(payload)
    to_encode.update({"exp": exp})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
