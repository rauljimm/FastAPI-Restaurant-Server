"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel

from app.db.database import get_db
from app.schemas.usuario import Token
from app.services.auth_service import authenticate_user, create_access_token

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Modelo para login con JSON
class LoginInput(BaseModel):
    username: str
    password: str

router = APIRouter(tags=["autenticación"])

@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Autenticar a un usuario y devolver un token de acceso.
    """
    try:
        # Log de la solicitud recibida
        body = await request.body()
        logger.debug(f"Cuerpo de la solicitud: {body}")
        logger.debug(f"Formulario recibido - username: {form_data.username}, password: {'*' * len(form_data.password) if form_data.password else 'vacío'}")
        
        # Autenticar usuario
        user = authenticate_user(db, form_data.username, form_data.password)
        logger.debug(f"Usuario autenticado: {user.username}, rol: {user.rol}")
        
        # Crear token
        access_token = create_access_token(username=user.username, rol=user.rol)
        logger.debug("Token creado exitosamente")
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as he:
        logger.error(f"Error HTTP: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        # Manejar cualquier error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de autenticación: {str(e)}"
        )

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_json(
    login_data: LoginInput,
    db: Session = Depends(get_db)
):
    """
    Autenticar a un usuario con credenciales JSON y devolver un token de acceso.
    """
    try:
        logger.debug(f"Login JSON - username: {login_data.username}")
        
        # Autenticar usuario
        user = authenticate_user(db, login_data.username, login_data.password)
        logger.debug(f"Usuario autenticado: {user.username}, rol: {user.rol}")
        
        # Crear token
        access_token = create_access_token(username=user.username, rol=user.rol)
        logger.debug("Token creado exitosamente")
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as he:
        logger.error(f"Error HTTP: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        # Manejar cualquier error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de autenticación: {str(e)}"
        ) 