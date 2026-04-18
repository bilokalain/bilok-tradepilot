"""Routes d'authentification — login, register, profil, mot de passe"""

from fastapi import APIRouter, Depends

from backend.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest,
    ResetPasswordRequest, ResetPasswordConfirm, UpdateProfileRequest,
    TokenResponse,
    authenticate_user, register_user, create_token,
    change_password, create_reset_token, reset_password_with_token,
    update_profile, require_auth, get_all_users,
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
async def get_profile(user: dict = Depends(require_auth)):
    """Retourne le profil de l'utilisateur connecté."""
    return user


@router.put("/me")
async def update_my_profile(req: UpdateProfileRequest, user: dict = Depends(require_auth)):
    """Met à jour le profil (nom)."""
    return update_profile(user["email"], req.name)


@router.post("/change-password")
async def change_my_password(req: ChangePasswordRequest, user: dict = Depends(require_auth)):
    """Change le mot de passe (utilisateur connecté)."""
    return change_password(user["email"], req.current_password, req.new_password)


@router.post("/forgot-password")
def forgot_password(req: ResetPasswordRequest):
    """Demande un token de réinitialisation."""
    token = create_reset_token(req.email)
    # En production : envoyer par email. Ici on retourne le token directement.
    if token:
        return {
            "message": "Si cet email existe, un lien de réinitialisation a été généré.",
            "reset_token": token,  # En prod, ne pas retourner ça — l'envoyer par email
            "expires_in_minutes": 30,
        }
    # Même réponse si l'email n'existe pas (sécurité)
    return {"message": "Si cet email existe, un lien de réinitialisation a été généré."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordConfirm):
    """Réinitialise le mot de passe avec un token."""
    return reset_password_with_token(req.token, req.new_password)


@router.get("/users")
def list_users():
    """Liste les utilisateurs inscrits."""
    return get_all_users()
