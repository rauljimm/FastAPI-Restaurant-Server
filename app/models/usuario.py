"""
Modelo de Usuario para la base de datos.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from app.db.database import Base
from app.core.enums import RolUsuario

class Usuario(Base):
    """Modelo que representa un usuario en el sistema"""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    nombre = Column(String)
    apellido = Column(String)
    rol = Column(String)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now(UTC))
    
    # Relaciones
    pedidos = relationship("Pedido", back_populates="camarero") 