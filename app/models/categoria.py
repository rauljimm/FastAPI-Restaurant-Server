"""
Modelo de Categoría para la base de datos.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base

class Categoria(Base):
    """Modelo que representa una categoría de productos"""
    __tablename__ = "categorias"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    descripcion = Column(String, nullable=True)
    
    # Relaciones
    productos = relationship("Producto", back_populates="categoria") 