"""
Modelo de Producto para la base de datos.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base

class Producto(Base):
    """Modelo que representa un producto en el menú"""
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    descripcion = Column(String, nullable=True)
    precio = Column(Float)
    tiempo_preparacion = Column(Integer, default=10)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    tipo = Column(String)
    imagen_url = Column(String, nullable=True)
    disponible = Column(Boolean, default=True)
    
    # Relaciones
    categoria = relationship("Categoria", back_populates="productos")
    detalles_pedido = relationship("DetallePedido", back_populates="producto") 