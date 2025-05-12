"""
Esquemas Pydantic para Mesa.
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.core.enums import EstadoMesa

class MesaBase(BaseModel):
    """Esquema base para datos de mesa"""
    numero: int = Field(..., gt=0, description="Número identificador de la mesa")
    capacidad: int = Field(..., gt=0, description="Capacidad de la mesa en personas")
    ubicacion: Optional[str] = Field(None, description="Ubicación de la mesa en el restaurante")

class MesaCreate(MesaBase):
    """Esquema para crear una nueva mesa"""
    pass

class MesaUpdate(BaseModel):
    """Esquema para actualizar una mesa existente"""
    numero: Optional[int] = Field(None, gt=0, description="Número identificador de la mesa")
    capacidad: Optional[int] = Field(None, gt=0, description="Capacidad de la mesa en personas")
    estado: Optional[EstadoMesa] = Field(None, description="Estado de la mesa")
    ubicacion: Optional[str] = Field(None, description="Ubicación de la mesa en el restaurante")
    metodo_pago: Optional[str] = Field(None, description="Método de pago usado al cerrar la mesa")

class Mesa(MesaBase):
    """Esquema para la respuesta de mesa"""
    id: int
    estado: EstadoMesa
    
    model_config = {"from_attributes": True}

class MesaResponse(Mesa):
    """Esquema para la respuesta completa de mesa"""
    # Incluye todos los campos de Mesa
    model_config = {"from_attributes": True} 