"""
Endpoints de gestión de categorías.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse
from app.services import categoria_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual, get_camarero_actual

router = APIRouter(
    prefix="/categorias",
    tags=["categorías"]
)

@router.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def create_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Crear una nueva categoría. (Admin only)
    """
    return categoria_service.create_categoria(db=db, categoria=categoria)

@router.get("/", response_model=List[CategoriaResponse])
def read_categorias(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Obtener todas las categorías. (Acceso público para pruebas)
    """
    categorias = categoria_service.get_categorias(db, skip=skip, limit=limit)
    return categorias

@router.get("/{categoria_id}", response_model=CategoriaResponse)
def read_categoria(
    categoria_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una categoría específica por ID. (Acceso público para pruebas)
    """
    return categoria_service.get_categoria_by_id(db, categoria_id=categoria_id)

@router.put("/{categoria_id}", response_model=CategoriaResponse)
def update_categoria(
    categoria_id: int,
    categoria: CategoriaUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Actualizar una categoría. (Admin only)
    """
    return categoria_service.update_categoria(db=db, categoria_id=categoria_id, categoria=categoria)

@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Eliminar una categoría. (Admin only)
    """
    categoria_service.delete_categoria(db=db, categoria_id=categoria_id)
    return {} 