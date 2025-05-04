"""
Modelo de Reserva para la base de datos.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from app.db.database import Base
from app.core.enums import EstadoReserva

class Reserva(Base):
    """Modelo que representa una reserva de mesa"""
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_nombre = Column(String)
    cliente_apellido = Column(String)
    cliente_telefono = Column(String)
    cliente_email = Column(String, nullable=True)
    fecha = Column(DateTime)
    duracion = Column(Integer, default=120)  # en minutos
    num_personas = Column(Integer)
    estado = Column(String, default=EstadoReserva.PENDIENTE)
    mesa_id = Column(Integer, ForeignKey("mesas.id"), nullable=True)
    observaciones = Column(String, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now(UTC))
    
    # Relaciones
    mesa = relationship("Mesa", back_populates="reservas") 