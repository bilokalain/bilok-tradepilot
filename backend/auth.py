"""Authentification JWT pour TradePilot

- Login avec email/password
- Token JWT (expire en 24h)
- Middleware pour protéger les routes
- Premier utilisateur créé automatiquement
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from backend.config.settings import settings

# Config
SECRET_KEY = settings.NEXTAUTH_SECRET if hasattr(settings, "NEXTAUTH_SECRET") and settings.NEXTAUTH_SECRET else "tradepilot-secret-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Store simple en mémoire (Phase 1 — PostgreSQL en Phase 2)
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
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def register_user(email: str, password: str, name: str = "") -> dict:
    if email in _users:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    _users[email] = {
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"email": email, "name": name}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = _users.get(email)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return {"email": user["email"], "name": user["name"]}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[dict]:
    """Dependency pour obtenir l'utilisateur courant.

    Retourne None si pas de token (routes publiques).
    Lève 401 si token invalide.
    """
    if credentials is None:
        return None

    email = decode_token(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )

    user = _users.get(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé",
        )
    return {"email": user["email"], "name": user["name"]}


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Dependency qui EXIGE un token valide."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )
    user = await get_current_user(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )
    return user


# Créer un utilisateur par défaut au démarrage
def init_default_user():
    if not _users:
        register_user("admin@tradepilot.local", "tradepilot2024", "Admin")


init_default_user()
