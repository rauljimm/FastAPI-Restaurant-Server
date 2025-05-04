"""
Service for Producto operations.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.producto import Producto
from app.models.categoria import Categoria
from app.schemas.producto import ProductoCreate, ProductoUpdate
from app.core.enums import TipoProducto
from app.core.websockets import safe_broadcast

def get_productos(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    categoria_id: Optional[int] = None,
    tipo: Optional[TipoProducto] = None,
    disponible: Optional[bool] = None
) -> List[Producto]:
    """Get products with optional filters"""
    query = db.query(Producto)
    
    if categoria_id is not None:
        query = query.filter(Producto.categoria_id == categoria_id)
    
    if tipo is not None:
        query = query.filter(Producto.tipo == tipo)
    
    if disponible is not None:
        query = query.filter(Producto.disponible == disponible)
    
    return query.offset(skip).limit(limit).all()

def get_producto_by_id(db: Session, producto_id: int) -> Producto:
    """Get a specific product by ID"""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

def create_producto(db: Session, producto: ProductoCreate) -> Producto:
    """Create a new product"""
    # Verify category exists
    categoria = db.query(Categoria).filter(Categoria.id == producto.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Create product
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # Notify via WebSockets
    mensaje = {
        "tipo": "actualizacion_menu",
        "accion": "crear",
        "producto_id": db_producto.id
    }
    safe_broadcast(mensaje, "camareros")
    safe_broadcast(mensaje, "cocina")
    
    return db_producto

def update_producto(db: Session, producto_id: int, producto: ProductoUpdate) -> Producto:
    """Update a product"""
    db_producto = get_producto_by_id(db, producto_id)
    
    # Verify category if changing
    if producto.categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == producto.categoria_id).first()
        if categoria is None:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Update fields
    for key, value in producto.model_dump(exclude_unset=True).items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    
    # Notify via WebSockets
    mensaje = {
        "tipo": "actualizacion_menu",
        "accion": "actualizar",
        "producto_id": db_producto.id
    }
    safe_broadcast(mensaje, "camareros")
    safe_broadcast(mensaje, "cocina")
    
    return db_producto

def delete_producto(db: Session, producto_id: int) -> None:
    """Delete a product"""
    db_producto = get_producto_by_id(db, producto_id)
    
    # Check if product is in active orders
    from app.models.pedido import DetallePedido, Pedido
    from app.core.enums import EstadoPedido
    
    pedidos_activos = db.query(DetallePedido).join(Pedido).filter(
        DetallePedido.producto_id == producto_id,
        Pedido.estado.in_([EstadoPedido.RECIBIDO, EstadoPedido.EN_PREPARACION])
    ).count()
    
    if pedidos_activos > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el producto porque está en {pedidos_activos} pedidos activos"
        )
    
    # Delete product
    db.delete(db_producto)
    db.commit()
    
    # Notify via WebSockets
    mensaje = {
        "tipo": "actualizacion_menu",
        "accion": "eliminar",
        "producto_id": producto_id
    }
    safe_broadcast(mensaje, "camareros")
    safe_broadcast(mensaje, "cocina") 