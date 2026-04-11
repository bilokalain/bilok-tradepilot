"""Authentification JWT pour TradePilot"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "tradepilot-secret-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)
_users: dict[str, dict] = {}


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_HOURS * 3600
    user: dict


def hash_password(password: str) -> str:
    return hashlib.sha256(f"tradepilot_{password}".encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
    except JWTError:
        return None


def register_user(email: str, password: str, name: str = "") -> dict:
    if email in _users:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    _users[email] = {"email": email, "password_hash": hash_password(password), "name": name}
    return {"email": email, "name": name}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = _users.get(email)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return {"email": user["email"], "name": user["name"]}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if credentials is None:
        return None
    email = decode_token(credentials.credentials)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = _users.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    return {"email": user["email"], "name": user["name"]}


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    user = await get_current_user(credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    return user


def init_default_user():
    if not _users:
        register_user("admin@tradepilot.local", "tradepilot2024", "Admin")


init_default_user()
