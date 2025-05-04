"""
Esquemas Pydantic para Mesa.
"""
from typing import Optional
from pydantic import BaseModel

from app.core.enums import EstadoMesa

class MesaBase(BaseModel):
    """Esquema base para datos de mesa"""
    numero: int
    capacidad: int
    ubicacion: Optional[str] = None

class MesaCreate(MesaBase):
    """Esquema para crear una nueva mesa"""
    pass

class MesaUpdate(BaseModel):
    """Esquema para actualizar una mesa"""
    capacidad: Optional[int] = None
    estado: Optional[EstadoMesa] = None
    ubicacion: Optional[str] = None

class MesaResponse(MesaBase):
    """Esquema para datos de respuesta de mesa"""
    id: int
    estado: str
    
    class Config:
        from_attributes = True 