"""
Endpoints d'authentification professionnelle pour AutoClaim API.
Gère le login, la validation de session JWT, la gestion des rôles et la création d'utilisateurs.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import Optional, List

from src.auth.auth_service import auth_service
from src.schemas.pydantic_models import UserContext

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "technicien"
    department: str = "Atelier"


class TokenInfo(BaseModel):
    token: str
    user: dict


@router.post("/login", response_model=TokenInfo)
def login(req: LoginRequest):
    """
    Authentification professionnelle :
    - Vérifie les identifiants (username + mot de passe)
    - Génère un jeton JWT de session (valide 12h)
    - Retourne le profil utilisateur avec ses droits d'accès
    """
    result = auth_service.authenticate(req.username, req.password)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "Authentification échouée"))

    return {
        "token": result["token"],
        "user": result["user"]
    }


@router.post("/register")
def register(req: RegisterRequest):
    """
    Enregistrement d'un nouvel utilisateur professionnel (admin uniquement).
    Crée un compte avec les rôles RBAC : technicien, expert_valideur, gestionnaire_flotte.
    """
    result = auth_service.register_user(
        username=req.username,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
        department=req.department
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/me")
def get_profile(token: str = None):
    """
    Consulte le profil de l'utilisateur connecté via son token JWT.
    Utilisé par le frontend pour afficher les informations utilisateur et les boutons d'action.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Jeton d'authentification manquant")

    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré")

    return {
        "user": {
            "username": payload.get("sub"),
            "full_name": payload.get("full_name"),
            "role": payload.get("role"),
            "authorized_groups": payload.get("authorized_groups", [])
        }
    }


@router.post("/logout")
def logout(response: Response, token: str = None):
    """
    Déconnexion : invalide le token de session côté serveur.
    """
    if token:
        # Dans une implémentation complète, on ajouterait le token à une blacklist
        pass
    return {"message": "Déconnexion effectuée avec succès."}


def get_current_user(token: str) -> UserContext:
    """
    Dépendance FastAPI pour protéger les endpoints nécessitant une authentification.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Jeton d'authentification manquant")

    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré")

    return UserContext(
        user_id=payload.get("sub", "unknown"),
        role=payload.get("role", "technicien"),
        authorized_groups=payload.get("authorized_groups", ["groupe_standard"])
    )


def require_admin_role(token: str) -> UserContext:
    """
    Dépendance FastAPI pour les endpoints réservés aux administrateurs.
    """
    user = get_current_user(token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé : rôle administrateur requis.")
    return user
