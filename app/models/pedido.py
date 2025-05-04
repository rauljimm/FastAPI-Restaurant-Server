"""
Modelos de Pedido y DetallePedido para la base de datos.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from app.db.database import Base
from app.core.enums import EstadoPedido

class Pedido(Base):
    """Modelo que representa un pedido"""
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"))
    camarero_id = Column(Integer, ForeignKey("usuarios.id"))
    estado = Column(String, default=EstadoPedido.RECIBIDO)
    fecha_creacion = Column(DateTime, default=datetime.now(UTC))
    fecha_actualizacion = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    total = Column(Float, default=0)
    observaciones = Column(String, nullable=True)
    
    # Relaciones
    mesa = relationship("Mesa", back_populates="pedidos")
    camarero = relationship("Usuario", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

class DetallePedido(Base):
    """Modelo que representa un detalle de línea en un pedido"""
    __tablename__ = "detalles_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    subtotal = Column(Float)
    estado = Column(String, default=EstadoPedido.RECIBIDO)
    observaciones = Column(String, nullable=True)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_pedido") 