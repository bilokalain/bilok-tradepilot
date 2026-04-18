"""Authentification JWT pour Bilok-TradePilot — comptes persistés en BDD"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "tradepilot-secret-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)

# Fichier de persistance des utilisateurs (simple et fiable)
USERS_FILE = Path("data/users.json")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    email: str


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_HOURS * 3600
    user: dict


def _load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_users(users: dict):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False))


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
    users = _load_users()
    if email in users:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire au moins 6 caractères")

    users[email] = {
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "is_admin": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    _save_users(users)
    return {"email": email, "name": name}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    users = _load_users()
    user = users.get(email)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return {"email": user["email"], "name": user.get("name", ""), "is_admin": user.get("is_admin", False)}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if credentials is None:
        return None
    email = decode_token(credentials.credentials)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    users = _load_users()
    user = users.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    return {"email": user["email"], "name": user.get("name", ""), "is_admin": user.get("is_admin", False)}


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    user = await get_current_user(credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    return user


def get_all_users() -> list[dict]:
    """Liste tous les utilisateurs (sans les mots de passe)."""
    users = _load_users()
    return [
        {"email": u["email"], "name": u.get("name", ""), "is_admin": u.get("is_admin", False), "created_at": u.get("created_at", "")}
        for u in users.values()
    ]


def change_password(email: str, current_password: str, new_password: str) -> dict:
    """Change le mot de passe d'un utilisateur authentifié."""
    users = _load_users()
    user = users.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit faire au moins 6 caractères")
    users[email]["password_hash"] = hash_password(new_password)
    users[email]["password_changed_at"] = datetime.utcnow().isoformat()
    _save_users(users)
    return {"message": "Mot de passe modifié avec succès"}


# Stockage temporaire des tokens de reset (en mémoire — suffisant pour un usage local)
_reset_tokens: dict[str, dict] = {}

RESET_TOKEN_EXPIRE_MINUTES = 30


def create_reset_token(email: str) -> Optional[str]:
    """Crée un token de réinitialisation pour un email existant."""
    users = _load_users()
    if email not in users:
        return None  # Ne pas révéler si l'email existe
    import secrets
    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {
        "email": email,
        "expires": (datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)).isoformat(),
    }
    return token


def reset_password_with_token(token: str, new_password: str) -> dict:
    """Réinitialise le mot de passe avec un token valide."""
    reset_data = _reset_tokens.get(token)
    if not reset_data:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")
    if datetime.utcnow() > datetime.fromisoformat(reset_data["expires"]):
        del _reset_tokens[token]
        raise HTTPException(status_code=400, detail="Token expiré")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire au moins 6 caractères")

    email = reset_data["email"]
    users = _load_users()
    if email not in users:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    users[email]["password_hash"] = hash_password(new_password)
    users[email]["password_changed_at"] = datetime.utcnow().isoformat()
    _save_users(users)
    del _reset_tokens[token]
    return {"message": "Mot de passe réinitialisé avec succès"}


def update_profile(email: str, name: str) -> dict:
    """Met à jour le profil d'un utilisateur."""
    users = _load_users()
    if email not in users:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    users[email]["name"] = name
    _save_users(users)
    return {"email": email, "name": name, "is_admin": users[email].get("is_admin", False)}


def set_user_admin(email: str, is_admin: bool) -> dict:
    """Définit ou retire le statut admin d'un utilisateur."""
    users = _load_users()
    if email not in users:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    users[email]["is_admin"] = is_admin
    _save_users(users)
    return {"email": email, "is_admin": is_admin}


def init_default_user():
    users = _load_users()
    if "admin@tradepilot.local" not in users:
        register_user("admin@tradepilot.local", "tradepilot2024", "Admin")
        # Marquer le compte par défaut comme admin
        users = _load_users()
        users["admin@tradepilot.local"]["is_admin"] = True
        _save_users(users)
    elif not users["admin@tradepilot.local"].get("is_admin"):
        users["admin@tradepilot.local"]["is_admin"] = True
        _save_users(users)


init_default_user()
