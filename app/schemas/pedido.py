"""
Esquemas Pydantic para Pedido y DetallePedido.
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.core.enums import EstadoPedido
from app.schemas.mesa import MesaResponse
from app.schemas.usuario import UsuarioResponse
from app.schemas.producto import ProductoResponse, ProductoResponseSimple

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
    
    model_config = {"from_attributes": True}

class DetallePedidoDetallado(DetallePedidoResponse):
    """Esquema para respuesta detallada de detalle de pedido incluyendo datos del producto"""
    producto: Optional[ProductoResponse] = None
    
    @field_validator('producto_id', mode='before')
    def ensure_producto_id_not_none(cls, v):
        """Asegurar que producto_id no sea None"""
        if v is None:
            return 0  # Valor predeterminado cuando el producto_id es None
        return v
    
    @field_validator('producto', mode='before')
    def handle_missing_product(cls, v, info):
        """Manejar el caso de producto inexistente o eliminado"""
        if v is None:
            # Crear un producto sustituto para evitar errores de validación
            from app.schemas.producto import ProductoResponseSimple
            from app.core.enums import TipoProducto
            
            # Extraer los datos del detalle para crear un sustituto informativo
            values = info.data
            producto_id = values.get('producto_id', 0)
            precio = values.get('precio_unitario', 0.0)
            
            # Crear un sustituto con información mínima
            return ProductoResponseSimple(
                id=producto_id,
                nombre="[Producto eliminado]",
                precio=precio,
                disponible=False
            )
        return v
    
    model_config = {"from_attributes": True}

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
    camarero_id: Optional[int] = None
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    observaciones: Optional[str] = None
    total: float
    
    model_config = {"from_attributes": True}

class PedidoDetallado(PedidoResponse):
    """Esquema para respuesta detallada de pedido incluyendo datos relacionados"""
    detalles: List[DetallePedidoDetallado]
    mesa: Optional[MesaResponse] = None
    camarero: Optional[UsuarioResponse] = None
    
    @field_validator('mesa', mode='before')
    def validate_mesa(cls, v, info):
        """Si mesa_id es None, la mesa también debe ser None"""
        values = info.data
        if 'mesa_id' in values and values['mesa_id'] is None:
            return None
        return v
    
    @field_validator('camarero', mode='before')
    def validate_camarero(cls, v, info):
        """Si camarero_id es None, el camarero también debe ser None"""
        values = info.data
        if 'camarero_id' in values and values['camarero_id'] is None:
            return None
        return v
    
    model_config = {"from_attributes": True} 