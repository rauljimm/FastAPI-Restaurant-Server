"""
Esquemas Pydantic para Cuenta.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json

class DetalleCuentaItem(BaseModel):
    """Esquema para un ítem dentro del detalle de la cuenta"""
    pedido_id: int
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    observaciones: Optional[str] = None

class CuentaBase(BaseModel):
    """Esquema base para datos de cuenta"""
    numero_mesa: int
    nombre_camarero: str
    total: float
    metodo_pago: Optional[str] = None
    detalles: List[DetalleCuentaItem] = []

class CuentaCreate(CuentaBase):
    """Esquema para crear una cuenta"""
    mesa_id: Optional[int] = None
    camarero_id: Optional[int] = None

class CuentaUpdate(BaseModel):
    """Esquema para actualizar una cuenta"""
    metodo_pago: Optional[str] = None

class CuentaResponse(CuentaBase):
    """Esquema para la respuesta de cuenta"""
    id: int
    mesa_id: Optional[int] = None
    camarero_id: Optional[int] = None
    fecha_cobro: datetime
    
    class Config:
        """Configuración para el esquema"""
        orm_mode = True
        
    @validator('detalles', pre=True)
    def parse_detalles(cls, v):
        """
        Validador para asegurar que detalles sea una lista de diccionarios.
        Si es un string JSON, lo convierte a una lista de diccionarios.
        Si es None o no es válido, devuelve una lista vacía.
        """
        if v is None:
            return []
            
        if isinstance(v, str):
            if not v:  # Si es una cadena vacía
                return []
                
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
                
        if isinstance(v, list):
            return v
            
        # Para cualquier otro caso, devolver lista vacía
        return [] 