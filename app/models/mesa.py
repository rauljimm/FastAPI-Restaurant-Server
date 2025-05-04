"""
Modelo de Mesa para la base de datos.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.core.enums import EstadoMesa

class Mesa(Base):
    """Modelo que representa una mesa en el restaurante"""
    __tablename__ = "mesas"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True)
    capacidad = Column(Integer)
    estado = Column(String, default=EstadoMesa.LIBRE)
    ubicacion = Column(String, nullable=True)
    
    # Relaciones
    pedidos = relationship("Pedido", back_populates="mesa")
    reservas = relationship("Reserva", back_populates="mesa") 