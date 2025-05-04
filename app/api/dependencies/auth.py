"""
Authentication dependencies for API endpoints.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt import PyJWTError
import jwt
from datetime import datetime, timedelta, UTC

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import TokenData
from app.core.enums import RolUsuario
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, TOKEN_URL

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

def crear_token_acceso(data: dict, expires_delta: timedelta = None):
    """Create a new access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_usuario_actual(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get the current authenticated user"""
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credenciales_exception
        token_data = TokenData(username=username, rol=payload.get("rol"))
    except PyJWTError:
        raise credenciales_exception
    usuario = db.query(Usuario).filter(Usuario.username == token_data.username).first()
    if usuario is None:
        raise credenciales_exception
    if not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return usuario

def get_admin_actual(usuario_actual: Usuario = Depends(get_usuario_actual)):
    """Verify the current user is an admin"""
    if usuario_actual.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción"
        )
    return usuario_actual

def get_camarero_actual(usuario_actual: Usuario = Depends(get_usuario_actual)):
    """Verify the current user is a waiter or admin"""
    if usuario_actual.rol != RolUsuario.CAMARERO and usuario_actual.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción"
        )
    return usuario_actual

def get_cocinero_actual(usuario_actual: Usuario = Depends(get_usuario_actual)):
    """Verify the current user is a cook or admin"""
    if usuario_actual.rol != RolUsuario.COCINERO and usuario_actual.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción"
        )
    return usuario_actual 