"""
Esquemas Pydantic para Producto.
"""
from typing import Optional
from pydantic import BaseModel

from app.core.enums import TipoProducto
from app.schemas.categoria import CategoriaResponse

class ProductoBase(BaseModel):
    """Esquema base para datos de producto"""
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    tiempo_preparacion: int
    categoria_id: int
    tipo: TipoProducto
    imagen_url: Optional[str] = None
    disponible: bool = True

class ProductoCreate(ProductoBase):
    """Esquema para crear un nuevo producto"""
    pass

class ProductoUpdate(BaseModel):
    """Esquema para actualizar un producto"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    tiempo_preparacion: Optional[int] = None
    categoria_id: Optional[int] = None
    tipo: Optional[TipoProducto] = None
    imagen_url: Optional[str] = None
    disponible: Optional[bool] = None

class ProductoResponse(ProductoBase):
    """Esquema para datos de respuesta de producto"""
    id: int
    
    model_config = {"from_attributes": True}

class ProductoResponseSimple(BaseModel):
    """Esquema simplificado para productos eliminados"""
    id: int
    nombre: str
    precio: float
    disponible: bool = False
    
    model_config = {"from_attributes": True}

class ProductoDetallado(ProductoResponse):
    """Esquema para respuesta detallada de producto incluyendo datos de categoría"""
    categoria: CategoriaResponse
    
    model_config = {"from_attributes": True} 