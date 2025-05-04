"""
Esquemas Pydantic para Reserva.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.core.enums import EstadoReserva
from app.schemas.mesa import MesaResponse

class ReservaBase(BaseModel):
    """Esquema base para datos de reserva"""
    cliente_nombre: str
    cliente_apellido: str
    cliente_telefono: str
    cliente_email: Optional[EmailStr] = None
    fecha: datetime
    duracion: Optional[int] = 120  # en minutos
    num_personas: int
    mesa_id: Optional[int] = None
    observaciones: Optional[str] = None

class ReservaCreate(ReservaBase):
    """Esquema para crear una nueva reserva"""
    pass

class ReservaUpdate(BaseModel):
    """Esquema para actualizar una reserva"""
    cliente_nombre: Optional[str] = None
    cliente_apellido: Optional[str] = None
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[EmailStr] = None
    fecha: Optional[datetime] = None
    duracion: Optional[int] = None
    num_personas: Optional[int] = None
    mesa_id: Optional[int] = None
    estado: Optional[EstadoReserva] = None
    observaciones: Optional[str] = None

class ReservaResponse(ReservaBase):
    """Esquema para datos de respuesta de reserva"""
    id: int
    estado: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class ReservaDetallada(ReservaResponse):
    """Esquema para respuesta detallada de reserva incluyendo datos de mesa"""
    mesa: Optional[MesaResponse] = None
    
    class Config:
        from_attributes = True 