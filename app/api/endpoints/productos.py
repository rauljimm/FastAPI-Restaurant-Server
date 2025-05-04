"""
Product management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse, ProductoDetallado
from app.services import producto_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual
from app.core.enums import TipoProducto

router = APIRouter(
    prefix="/productos",
    tags=["productos"],
    dependencies=[Depends(get_usuario_actual)]
)

@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Create a new product. (Admin only)
    """
    return producto_service.create_producto(db=db, producto=producto)

@router.get("/", response_model=List[ProductoResponse])
def read_productos(
    skip: int = 0,
    limit: int = 100,
    categoria_id: Optional[int] = None,
    tipo: Optional[TipoProducto] = None,
    disponible: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Get all products with optional filters.
    """
    productos = producto_service.get_productos(
        db, 
        skip=skip, 
        limit=limit,
        categoria_id=categoria_id,
        tipo=tipo,
        disponible=disponible
    )
    return productos

@router.get("/{producto_id}", response_model=ProductoDetallado)
def read_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Get a specific product by ID including its category.
    """
    return producto_service.get_producto_by_id(db, producto_id=producto_id)

@router.put("/{producto_id}", response_model=ProductoResponse)
def update_producto(
    producto_id: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Update a product. (Admin only)
    """
    return producto_service.update_producto(db=db, producto_id=producto_id, producto=producto)

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Delete a product. (Admin only)
    """
    producto_service.delete_producto(db=db, producto_id=producto_id)
    return {} 