"""
Endpoints de gestión de productos.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse, ProductoDetallado
from app.services import producto_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual, get_camarero_actual
from app.core.enums import TipoProducto

router = APIRouter(
    prefix="/productos",
    tags=["productos"]
)

@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Crear un nuevo producto. (Admin only)
    """
    return producto_service.create_producto(db=db, producto=producto)

@router.get("/", response_model=List[ProductoResponse])
def read_productos(
    skip: int = 0,
    limit: int = 100,
    categoria_id: Optional[int] = None,
    tipo: Optional[TipoProducto] = None,
    disponible: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Obtener todos los productos con filtros opcionales.
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
    db: Session = Depends(get_db)
):
    """
    Obtener un producto específico por ID incluyendo su categoría.
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
    Actualizar un producto. (Admin only)
    """
    return producto_service.update_producto(db=db, producto_id=producto_id, producto=producto)

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Eliminar un producto. (Admin only)
    """
    producto_service.delete_producto(db=db, producto_id=producto_id)
    return {} 