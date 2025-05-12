"""
Esquemas Pydantic para Usuario.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.core.enums import RolUsuario

class UsuarioBase(BaseModel):
    """Esquema base para datos de usuario"""
    email: EmailStr
    nombre: str
    apellido: str
    rol: RolUsuario

class UsuarioCreate(UsuarioBase):
    """Esquema para crear un nuevo usuario"""
    username: str
    password: str

class UsuarioUpdate(BaseModel):
    """Esquema para actualizar un usuario"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    """Esquema para datos de respuesta de usuario"""
    id: int
    username: str
    activo: bool
    fecha_creacion: datetime
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    """Esquema para token de autenticación"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Esquema para datos del token"""
    username: Optional[str] = None
    rol: Optional[str] = None 