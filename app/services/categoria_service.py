"""
Servicio para operaciones de Categoría.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.categoria import Categoria
from app.models.producto import Producto
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate

def get_categorias(db: Session, skip: int = 0, limit: int = 100) -> List[Categoria]:
    """Obtener todas las categorías con paginación"""
    return db.query(Categoria).offset(skip).limit(limit).all()

def get_categoria_by_id(db: Session, categoria_id: int) -> Optional[Categoria]:
    """Obtener una categoría específica por ID"""
    categoria = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

def get_categoria_by_nombre(db: Session, nombre: str) -> Optional[Categoria]:
    """Obtener una categoría por nombre"""
    return db.query(Categoria).filter(Categoria.nombre == nombre).first()

def create_categoria(db: Session, categoria: CategoriaCreate) -> Categoria:
    """Crear una nueva categoría"""
    # Check if category already exists
    db_categoria = get_categoria_by_nombre(db, categoria.nombre)
    if db_categoria:
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    
    # Create category
    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def update_categoria(db: Session, categoria_id: int, categoria: CategoriaUpdate) -> Categoria:
    """Actualizar una categoría"""
    db_categoria = get_categoria_by_id(db, categoria_id)
    
    # Check if new name is unique
    if categoria.nombre is not None:
        nombre_existente = db.query(Categoria).filter(
            Categoria.nombre == categoria.nombre,
            Categoria.id != categoria_id
        ).first()
        if nombre_existente:
            raise HTTPException(status_code=400, detail="El nombre de categoría ya existe")
        db_categoria.nombre = categoria.nombre
    
    # Update description if provided
    if categoria.descripcion is not None:
        db_categoria.descripcion = categoria.descripcion
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def delete_categoria(db: Session, categoria_id: int) -> None:
    """Eliminar una categoría"""
    db_categoria = get_categoria_by_id(db, categoria_id)
    
    # Check if products are associated with this category
    productos_asociados = db.query(Producto).filter(
        Producto.categoria_id == categoria_id
    ).count()
    
    if productos_asociados > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la categoría porque tiene {productos_asociados} productos asociados"
        )
    
    db.delete(db_categoria)
    db.commit() 