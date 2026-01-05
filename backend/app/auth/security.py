from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ⚠️ En prod: mets ça dans une variable d'env
JWT_SECRET = "CHANGE_ME_SUPER_SECRET"
JWT_ALG = "HS256"
JWT_EXPIRES_MIN = 60 * 24  # 24h

def hash_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return PWD_CONTEXT.verify(password, password_hash)

def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MIN)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
