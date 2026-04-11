"""Routes d'authentification"""

from fastapi import APIRouter

from backend.auth import (
    LoginRequest, RegisterRequest, TokenResponse,
    authenticate_user, register_user, create_token,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_token(user["email"])
    return TokenResponse(
        access_token=token,
        user=user,
    )


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    user = register_user(req.email, req.password, req.name)
    token = create_token(user["email"])
    return TokenResponse(
        access_token=token,
        user=user,
    )


@router.get("/me")
def get_me():
    """Route publique pour tester — en production, utiliser require_auth."""
    return {"message": "Utilisez le header Authorization: Bearer <token>"}
