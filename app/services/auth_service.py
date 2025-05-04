"""
Servicio para operaciones de autenticación.
"""
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.api.dependencies.auth import crear_token_acceso
from app.core.security import verificar_password
from app.services.usuario_service import get_usuario_by_username
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES

def authenticate_user(db: Session, username: str, password: str) -> Usuario:
    """
    Autentica a un usuario verificando nombre de usuario y contraseña.
    Devuelve el usuario si la autenticación es exitosa.
    Lanza una excepción HTTP si la autenticación falla.
    """
    user = get_usuario_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verificar_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    return user

def create_access_token(username: str, rol: str, expires_delta: timedelta = None) -> str:
    """
    Crea un nuevo token de acceso JWT para el usuario autenticado.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return crear_token_acceso(
        data={"sub": username, "rol": rol},
        expires_delta=expires_delta
    ) 