"""
Endpoints de gestión de usuarios.
"""
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services import usuario_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual
from app.core.enums import RolUsuario

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(get_usuario_actual)]
)

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Crear un nuevo usuario. (Admin only)
    """
    return usuario_service.create_usuario(db=db, usuario=usuario)

@router.get("/", response_model=List[UsuarioResponse])
def read_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Obtener todos los usuarios. (Admin only)
    """
    usuarios = usuario_service.get_usuarios(db, skip=skip, limit=limit)
    return usuarios

@router.get("/me", response_model=UsuarioResponse)
def read_user_me(current_user: Usuario = Depends(get_usuario_actual)):
    """
    Obtener información del usuario actual.
    """
    return current_user

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def read_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener un usuario específico por ID.
    - Los usuarios pueden obtener su propia información
    - Los administradores pueden obtener la información de cualquier usuario
    """
    # Los usuarios solo pueden ver su propia información a menos que sean administradores
    if current_user.id != usuario_id and current_user.rol != RolUsuario.ADMIN:
        return get_admin_actual(current_user)
    
    usuario = usuario_service.get_usuario_by_id(db, usuario_id=usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return usuario

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(
    usuario_id: int,
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Actualizar un usuario.
    - Los usuarios pueden actualizar su propia información (excepto rol)
    - Los administradores pueden actualizar la información de cualquier usuario
    """
    is_admin = current_user.rol == RolUsuario.ADMIN
    return usuario_service.update_usuario(
        db=db, 
        usuario_id=usuario_id, 
        usuario=usuario, 
        current_user_id=current_user.id, 
        is_admin=is_admin
    )

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Eliminar un usuario. (Admin only)
    """
    usuario_service.delete_usuario(db=db, usuario_id=usuario_id)
    return {}  # Devolver un diccionario vacío en lugar de None para evitar errores de validación 