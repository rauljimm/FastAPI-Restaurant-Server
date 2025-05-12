"""
Esquemas Pydantic para Categoría.
"""
from typing import Optional
from pydantic import BaseModel

class CategoriaBase(BaseModel):
    """Esquema base para datos de categoría"""
    nombre: str
    descripcion: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    """Esquema para crear una nueva categoría"""
    pass

class CategoriaUpdate(BaseModel):
    """Esquema para actualizar una categoría"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class CategoriaResponse(CategoriaBase):
    """Esquema para datos de respuesta de categoría"""
    id: int
    
    model_config = {"from_attributes": True} 