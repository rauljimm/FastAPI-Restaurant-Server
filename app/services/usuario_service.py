"""
Service for Usuario operations.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.core.security import get_password_hash
from app.core.enums import RolUsuario

def get_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
    """Get all users with pagination"""
    return db.query(Usuario).offset(skip).limit(limit).all()

def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Get a specific user by ID"""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def get_usuario_by_username(db: Session, username: str) -> Optional[Usuario]:
    """Get a specific user by username"""
    return db.query(Usuario).filter(Usuario.username == username).first()

def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Get a specific user by email"""
    return db.query(Usuario).filter(Usuario.email == email).first()

def create_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
    """Create a new user"""
    # Check if username already exists
    db_usuario = get_usuario_by_username(db, usuario.username)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    # Check if email already exists
    db_email = get_usuario_by_email(db, usuario.email)
    if db_email:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Hash the password
    hashed_password = get_password_hash(usuario.password)
    
    # Create the user
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
    """Update a user"""
    db_usuario = get_usuario_by_id(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Users can only update their own info, admins can update anyone
    if current_user_id != usuario_id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para realizar esta acción"
        )
    
    # Non-admin users cannot change their own role
    if current_user_id == usuario_id and not is_admin and usuario.rol is not None:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para cambiar su rol"
        )
    
    # Check if email is unique
    if usuario.email is not None:
        db_email = get_usuario_by_email(db, usuario.email)
        if db_email and db_email.id != usuario_id:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        db_usuario.email = usuario.email
    
    # Update password if provided
    if usuario.password is not None:
        db_usuario.hashed_password = get_password_hash(usuario.password)
    
    # Update other fields
    if usuario.nombre is not None:
        db_usuario.nombre = usuario.nombre
    
    if usuario.apellido is not None:
        db_usuario.apellido = usuario.apellido
    
    # Only admins can change roles and active status
    if is_admin:
        if usuario.rol is not None:
            db_usuario.rol = usuario.rol
        
        if usuario.activo is not None:
            db_usuario.activo = usuario.activo
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: int) -> None:
    """Delete a user"""
    db_usuario = get_usuario_by_id(db, usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Prevent deleting the last admin
    if db_usuario.rol == RolUsuario.ADMIN:
        admin_count = db.query(Usuario).filter(Usuario.rol == RolUsuario.ADMIN, Usuario.activo == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="No se puede eliminar al último administrador")
    
    db.delete(db_usuario)
    db.commit() 