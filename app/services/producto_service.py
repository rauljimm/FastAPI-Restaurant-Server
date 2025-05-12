"""
Servicio para operaciones de Producto.
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
    """Obtener productos con filtros opcionales"""
    query = db.query(Producto)
    
    if categoria_id is not None:
        query = query.filter(Producto.categoria_id == categoria_id)
    
    if tipo is not None:
        query = query.filter(Producto.tipo == tipo)
    
    if disponible is not None:
        query = query.filter(Producto.disponible == disponible)
    
    return query.offset(skip).limit(limit).all()

def get_producto_by_id(db: Session, producto_id: int) -> Producto:
    """Obtener un producto específico por ID"""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

def create_producto(db: Session, producto: ProductoCreate) -> Producto:
    """Crear un nuevo producto"""
    # Verificar si la categoría existe
    categoria = db.query(Categoria).filter(Categoria.id == producto.categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Crear producto
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # Notificar via WebSockets
    mensaje = {
        "tipo": "actualizacion_menu",
        "accion": "crear",
        "producto_id": db_producto.id
    }
    safe_broadcast(mensaje, "camareros")
    safe_broadcast(mensaje, "cocina")
    
    return db_producto

def update_producto(db: Session, producto_id: int, producto: ProductoUpdate) -> Producto:
    """Actualizar un producto"""
    db_producto = get_producto_by_id(db, producto_id)
    
    # Verificar categoría si se está cambiando
    if producto.categoria_id is not None:
        categoria = db.query(Categoria).filter(Categoria.id == producto.categoria_id).first()
        if categoria is None:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Actualizar campos
    for key, value in producto.model_dump(exclude_unset=True).items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    
    # Notificar via WebSockets
    mensaje = {
        "tipo": "actualizacion_menu",
        "accion": "actualizar",
        "producto_id": db_producto.id
    }
    safe_broadcast(mensaje, "camareros")
    safe_broadcast(mensaje, "cocina")
    
    return db_producto

def delete_producto(db: Session, producto_id: int) -> None:
    """Eliminar un producto"""
    db_producto = get_producto_by_id(db, producto_id)
    
    # Verificar si el producto está en pedidos activos
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
    
    # Para pedidos históricos (entregados o cancelados), mantener la referencia pero evitar errores de FK
    detalles_historicos = db.query(DetallePedido).join(Pedido).filter(
        DetallePedido.producto_id == producto_id,
        Pedido.estado.in_([EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO, EstadoPedido.LISTO])
    ).all()
    
    # Conservar información del producto para pedidos históricos
    nombre_producto = db_producto.nombre
    precio_producto = db_producto.precio
    tipo_producto = db_producto.tipo
    
    # Crear una nota para cada detalle histórico
    for detalle in detalles_historicos:
        detalle_obs = detalle.observaciones or ""
        detalle.observaciones = f"{detalle_obs}\n[Producto eliminado: {nombre_producto}, ${precio_producto}]".strip()
        db.add(detalle)
    
    # Gestionar la referencia en el historial de cuentas
    from app.models.cuenta import Cuenta
    import json
    
    # Obtener todas las cuentas que podrían contener referencias al producto
    cuentas = db.query(Cuenta).all()
    for cuenta in cuentas:
        # Procesar detalles de la cuenta (convertir de JSON si es necesario)
        if isinstance(cuenta.detalles, str):
            try:
                detalles = json.loads(cuenta.detalles)
            except json.JSONDecodeError:
                detalles = []
        else:
            detalles = cuenta.detalles if cuenta.detalles else []
        
        # Verificar si hay cambios que hacer
        modificado = False
        
        # Si detalles es una lista, procesar cada elemento
        if isinstance(detalles, list):
            for detalle in detalles:
                # Si el detalle contiene el producto a eliminar, conservar la información
                if isinstance(detalle, dict) and detalle.get('producto_id') == producto_id:
                    # Marcar el producto como eliminado pero mantener sus datos
                    detalle['producto_eliminado'] = True
                    detalle['nombre_producto_original'] = nombre_producto
                    modificado = True
        
        # Si hubo modificaciones, guardar los cambios
        if modificado:
            cuenta.detalles = json.dumps(detalles)
            db.add(cuenta)
    
    # Guardar los cambios en las cuentas y detalles antes de eliminar el producto
    db.commit()
    
    # Eliminar producto
    db.delete(db_producto)
    db.commit()
    
    # Notificar via WebSockets
    mensaje = {
        "tipo": "actualizacion_menu",
        "accion": "eliminar",
        "producto_id": producto_id
    }
    safe_broadcast(mensaje, "camareros")
    safe_broadcast(mensaje, "cocina") 