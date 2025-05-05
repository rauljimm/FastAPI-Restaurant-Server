"""
Esquemas Pydantic para Pedido y DetallePedido.
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, validator

from app.core.enums import EstadoPedido
from app.schemas.mesa import MesaResponse
from app.schemas.usuario import UsuarioResponse
from app.schemas.producto import ProductoResponse

class DetallePedidoBase(BaseModel):
    """Esquema base para datos de detalle de pedido"""
    producto_id: int
    cantidad: int
    observaciones: Optional[str] = None

class DetallePedidoCreate(DetallePedidoBase):
    """Esquema para crear un nuevo detalle de pedido"""
    pass

class DetallePedidoUpdate(BaseModel):
    """Esquema para actualizar un detalle de pedido"""
    cantidad: Optional[int] = None
    estado: Optional[EstadoPedido] = None
    observaciones: Optional[str] = None

class DetallePedidoResponse(BaseModel):
    """Esquema para datos de respuesta de detalle de pedido"""
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float
    estado: str
    observaciones: Optional[str] = None
    
    class Config:
        from_attributes = True

class DetallePedidoDetallado(DetallePedidoResponse):
    """Esquema para respuesta detallada de detalle de pedido incluyendo datos del producto"""
    producto: ProductoResponse
    
    class Config:
        from_attributes = True

class PedidoBase(BaseModel):
    """Esquema base para datos de pedido"""
    mesa_id: int
    observaciones: Optional[str] = None

class PedidoCreate(PedidoBase):
    """Esquema para crear un nuevo pedido"""
    detalles: List[DetallePedidoCreate]

class PedidoUpdate(BaseModel):
    """Esquema para actualizar un pedido"""
    estado: Optional[EstadoPedido] = None
    observaciones: Optional[str] = None

class PedidoResponse(BaseModel):
    """Esquema para datos de respuesta de pedido"""
    id: int
    mesa_id: Optional[int] = None
    camarero_id: int
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    observaciones: Optional[str] = None
    total: float
    
    class Config:
        from_attributes = True

class PedidoDetallado(PedidoResponse):
    """Esquema para respuesta detallada de pedido incluyendo datos relacionados"""
    detalles: List[DetallePedidoDetallado]
    mesa: Optional[MesaResponse] = None
    camarero: UsuarioResponse
    
    @validator('mesa', pre=True)
    def validate_mesa(cls, v, values):
        """Si mesa_id es None, la mesa también debe ser None"""
        if 'mesa_id' in values and values['mesa_id'] is None:
            return None
        return v
    
    class Config:
        from_attributes = True 