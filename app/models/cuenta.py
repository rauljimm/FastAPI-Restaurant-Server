"""
Modelo de Cuenta para la base de datos.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from app.db.database import Base

class Cuenta(Base):
    """Modelo que representa el historial de cuentas cobradas"""
    __tablename__ = "cuentas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información de la mesa (incluso si se elimina posteriormente)
    mesa_id = Column(Integer, ForeignKey("mesas.id", ondelete="SET NULL"), nullable=True)
    numero_mesa = Column(Integer, nullable=False)  # Guardamos el número de mesa para referencia histórica
    
    # Información del camarero que cobró la cuenta
    camarero_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    nombre_camarero = Column(String, nullable=False)  # Guardamos el nombre para referencia histórica
    
    # Información temporal
    fecha_cobro = Column(DateTime, default=datetime.now(UTC), nullable=False)
    
    # Información económica
    total = Column(Float, nullable=False)
    metodo_pago = Column(String, nullable=True)
    
    # Detalle de la cuenta (IDs de pedidos, productos, cantidades, precios)
    detalles = Column(JSON, nullable=False)
    
    # Relaciones (opcionales, si la entidad existe)
    mesa = relationship("Mesa", backref="cuentas_historicas")
    camarero = relationship("Usuario", backref="cuentas_cobradas") 