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


@router.get("/users")
def list_users():
    """Liste les utilisateurs inscrits."""
    from backend.auth import get_all_users
    return get_all_users()
