"""
Servicio para operaciones de Usuario.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.core.security import get_password_hash
from app.core.enums import RolUsuario

def get_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
    """Obtener todos los usuarios con paginación"""
    return db.query(Usuario).offset(skip).limit(limit).all()

def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Obtener un usuario específico por ID"""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def get_usuario_by_username(db: Session, username: str) -> Optional[Usuario]:
    """Obtener un usuario específico por nombre de usuario"""
    return db.query(Usuario).filter(Usuario.username == username).first()

def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Obtener un usuario específico por email"""
    return db.query(Usuario).filter(Usuario.email == email).first()

def create_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
    """Crear un nuevo usuario"""
    # Verificar si el nombre de usuario ya existe
    db_usuario = get_usuario_by_username(db, usuario.username)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    # Verificar si el email ya existe
    db_email = get_usuario_by_email(db, usuario.email)
    if db_email:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Hashear la contraseña
    hashed_password = get_password_hash(usuario.password)
    
    # Crear el usuario
    db_usuario = Usuario(
        username=usuario.username,
        email=usuario.email,
        hashed_password=hashed_password,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        rol=usuario.rol
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def update_usuario(db: Session, usuario_id: int, usuario: UsuarioUpdate, current_user_id: int, is_admin: bool) -> Usuario:
    """Actualizar un usuario"""
    db_usuario = get_usuario_by_id(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Los usuarios solo pueden actualizar su propia información, los administradores pueden actualizar a cualquier usuario
    if current_user_id != usuario_id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para realizar esta acción"
        )
    
    # Los usuarios no administradores no pueden cambiar su propio rol
    if current_user_id == usuario_id and not is_admin and usuario.rol is not None:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para cambiar su rol"
        )
    
    # Verificar si el email es único
    if usuario.email is not None:
        db_email = get_usuario_by_email(db, usuario.email)
        if db_email and db_email.id != usuario_id:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        db_usuario.email = usuario.email
    
    # Actualizar la contraseña si se proporciona
    if usuario.password is not None:
        db_usuario.hashed_password = get_password_hash(usuario.password)
    
    # Actualizar otros campos
    if usuario.nombre is not None:
        db_usuario.nombre = usuario.nombre
    
    if usuario.apellido is not None:
        db_usuario.apellido = usuario.apellido
    
    # Solo los administradores pueden cambiar roles y estado activo
    if is_admin:
        if usuario.rol is not None:
            db_usuario.rol = usuario.rol
        
        if usuario.activo is not None:
            db_usuario.activo = usuario.activo
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: int) -> None:
    """Eliminar un usuario"""
    db_usuario = get_usuario_by_id(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Prevenir la eliminación del último administrador
    if db_usuario.rol == RolUsuario.ADMIN:
        admin_count = db.query(Usuario).filter(Usuario.rol == RolUsuario.ADMIN, Usuario.activo == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="No se puede eliminar al último administrador")
    
    db.delete(db_usuario)
    db.commit() 