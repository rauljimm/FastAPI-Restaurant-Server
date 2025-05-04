"""
Service for Pedido operations.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, UTC

from app.models.pedido import Pedido, DetallePedido
from app.models.mesa import Mesa
from app.models.usuario import Usuario
from app.models.producto import Producto
from app.schemas.pedido import PedidoCreate, PedidoUpdate, DetallePedidoCreate, DetallePedidoUpdate
from app.core.enums import EstadoPedido, EstadoMesa
from app.core.websockets import safe_broadcast, log_event

def get_pedidos(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    estado: Optional[EstadoPedido] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    mesa_id: Optional[int] = None,
    camarero_id: Optional[int] = None,
    current_user: Usuario = None
) -> List[Pedido]:
    """Get orders with optional filters"""
    query = db.query(Pedido)
    
    # Apply filters
    if estado is not None:
        query = query.filter(Pedido.estado == estado)
    
    if fecha_inicio is not None:
        query = query.filter(Pedido.fecha_creacion >= fecha_inicio)
    
    if fecha_fin is not None:
        query = query.filter(Pedido.fecha_creacion <= fecha_fin)
    
    if mesa_id is not None:
        query = query.filter(Pedido.mesa_id == mesa_id)
    
    # Apply user-based filtering
    if current_user is not None:
        from app.core.enums import RolUsuario
        
        if current_user.rol == RolUsuario.CAMARERO:
            # Waiters can only see their own orders
            query = query.filter(Pedido.camarero_id == current_user.id)
        elif current_user.rol == RolUsuario.ADMIN and camarero_id is not None:
            # Admins can filter by specific waiter
            query = query.filter(Pedido.camarero_id == camarero_id)
    
    # Order by creation date (newest first)
    query = query.order_by(Pedido.fecha_creacion.desc())
    
    return query.offset(skip).limit(limit).all()

def get_pedido_by_id(db: Session, pedido_id: int, current_user: Usuario = None) -> Pedido:
    """Get a specific order by ID"""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verify permissions
    if current_user is not None:
        from app.core.enums import RolUsuario
        
        if current_user.rol == RolUsuario.CAMARERO and pedido.camarero_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para ver este pedido"
            )
    
    return pedido

def create_pedido(db: Session, pedido: PedidoCreate, camarero_id: int) -> Pedido:
    """Create a new order"""
    # Verify table exists
    mesa = db.query(Mesa).filter(Mesa.id == pedido.mesa_id).first()
    if mesa is None:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    
    # Check if table is available
    if mesa.estado not in [EstadoMesa.LIBRE, EstadoMesa.OCUPADA]:
        raise HTTPException(status_code=400, detail="La mesa no está disponible")
    
    # Check if there are products in the order
    if not pedido.detalles:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos un producto")
    
    # Create order
    db_pedido = Pedido(
        mesa_id=pedido.mesa_id,
        camarero_id=camarero_id,
        observaciones=pedido.observaciones
    )
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    
    # Set table as occupied
    mesa.estado = EstadoMesa.OCUPADA
    db.commit()
    
    # Add order details
    total_pedido = 0.0
    for detalle in pedido.detalles:
        db_producto = db.query(Producto).filter(
            Producto.id == detalle.producto_id,
            Producto.disponible == True
        ).first()
        
        if db_producto is None:
            # If product doesn't exist or is not available, delete the order
            db.delete(db_pedido)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Producto {detalle.producto_id} no encontrado o no disponible")
        
        # Create order detail
        subtotal = db_producto.precio * detalle.cantidad
        db_detalle = DetallePedido(
            pedido_id=db_pedido.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            precio_unitario=db_producto.precio,
            subtotal=subtotal,
            observaciones=detalle.observaciones
        )
        db.add(db_detalle)
        total_pedido += subtotal
    
    # Update order total
    db_pedido.total = total_pedido
    db.commit()
    db.refresh(db_pedido)
    
    # Notify kitchen about new order
    camarero = db.query(Usuario).filter(Usuario.id == camarero_id).first()
    mensaje = {
        "tipo": "nuevo_pedido",
        "pedido_id": db_pedido.id,
        "mesa": mesa.numero,
        "camarero": f"{camarero.nombre} {camarero.apellido}",
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "cocina")
    
    return db_pedido

def update_pedido(db: Session, pedido_id: int, pedido: PedidoUpdate, current_user: Usuario) -> Pedido:
    """Update an order"""
    from app.core.enums import RolUsuario
    
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Check permissions for waiters
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para actualizar este pedido"
        )
    
    # Cooks can only change status to en_preparacion or listo
    if current_user.rol == RolUsuario.COCINERO:
        if pedido.estado not in [EstadoPedido.EN_PREPARACION, EstadoPedido.LISTO]:
            raise HTTPException(
                status_code=403,
                detail="Los cocineros solo pueden cambiar el estado a 'en_preparacion' o 'listo'"
            )
    
    # Update fields
    for key, value in pedido.model_dump(exclude_unset=True).items():
        setattr(db_pedido, key, value)
    
    # Si el estado cambia a entregado o cancelado, se permite que la mesa se libere
    # Ahora TODOS los usuarios (incluidos los camareros) pueden cambiar el estado de una mesa a LIBRE
    # cuando se han entregado todos los pedidos de la mesa
    if pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        db_mesa = db_pedido.mesa
        if db_mesa.estado == EstadoMesa.OCUPADA:
            # Check if there are other active orders for this table
            otros_pedidos_activos = db.query(Pedido).filter(
                Pedido.mesa_id == db_mesa.id,
                Pedido.id != pedido_id,
                Pedido.estado.in_([EstadoPedido.RECIBIDO, EstadoPedido.EN_PREPARACION, EstadoPedido.LISTO])
            ).count()
            
            if otros_pedidos_activos == 0:
                db_mesa.estado = EstadoMesa.LIBRE
                
                # Registrar en log el cambio de estado y el usuario que lo hizo
                log_event(f"Mesa {db_mesa.id} (#{db_mesa.numero}) cambiada a LIBRE por {current_user.username} [{current_user.rol}] al entregar el pedido {pedido_id}", "info")
    
    db.commit()
    db.refresh(db_pedido)
    
    # Notify about order update
    mensaje = {
        "tipo": "actualizacion_pedido",
        "pedido_id": db_pedido.id,
        "estado": db_pedido.estado,
        "mesa": db_pedido.mesa.numero,
        "hora": datetime.now(UTC).isoformat()
    }
    
    if current_user.rol == RolUsuario.COCINERO:
        # If cook changes status, notify waiters
        safe_broadcast(mensaje, "camareros")
    else:
        # If waiter/admin changes status, notify kitchen
        safe_broadcast(mensaje, "cocina")
    
    return db_pedido

def update_detalle_pedido(
    db: Session, 
    pedido_id: int, 
    detalle_id: int, 
    detalle: DetallePedidoUpdate, 
    current_user: Usuario
) -> DetallePedido:
    """Update an order detail"""
    from app.core.enums import RolUsuario
    
    # Verify order exists
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Check permissions for waiters
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para actualizar este pedido"
        )
    
    # Check if order is not already delivered or canceled
    if db_pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar un pedido entregado o cancelado"
        )
    
    # Verify order detail exists and belongs to order
    db_detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    
    if db_detalle is None:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    
    # Cooks can only change status
    if current_user.rol == RolUsuario.COCINERO:
        if detalle.estado is None:
            raise HTTPException(
                status_code=400,
                detail="Debe especificar un estado para el detalle"
            )
        
        if detalle.estado not in [EstadoPedido.EN_PREPARACION, EstadoPedido.LISTO]:
            raise HTTPException(
                status_code=403,
                detail="Los cocineros solo pueden cambiar el estado a 'en_preparacion' o 'listo'"
            )
        
        db_detalle.estado = detalle.estado
    else:
        # Waiters and admins can update everything
        if detalle.cantidad is not None:
            if detalle.cantidad <= 0:
                raise HTTPException(status_code=400, detail="La cantidad debe ser mayor que cero")
            
            # Recalculate subtotal
            db_detalle.cantidad = detalle.cantidad
            db_detalle.subtotal = db_detalle.precio_unitario * detalle.cantidad
            
            # Update order total
            nuevo_total = db.query(func.sum(DetallePedido.subtotal)).filter(
                DetallePedido.pedido_id == pedido_id
            ).scalar() or 0.0
            
            db_pedido.total = nuevo_total
        
        if detalle.estado is not None:
            db_detalle.estado = detalle.estado
        
        if detalle.observaciones is not None:
            db_detalle.observaciones = detalle.observaciones
    
    # Update order update timestamp
    db_pedido.fecha_actualizacion = datetime.now(UTC)
    
    db.commit()
    db.refresh(db_detalle)
    
    # Notify about detail update
    mensaje = {
        "tipo": "actualizacion_detalle",
        "pedido_id": db_pedido.id,
        "detalle_id": db_detalle.id,
        "producto": db_detalle.producto.nombre,
        "estado": db_detalle.estado,
        "mesa": db_pedido.mesa.numero,
        "hora": datetime.now(UTC).isoformat()
    }
    
    if current_user.rol == RolUsuario.COCINERO:
        safe_broadcast(mensaje, "camareros")
    else:
        safe_broadcast(mensaje, "cocina")
    
    return db_detalle

def create_detalle_pedido(
    db: Session, 
    pedido_id: int, 
    detalle: DetallePedidoCreate, 
    current_user: Usuario
) -> DetallePedido:
    """Add a new detail to an existing order"""
    from app.core.enums import RolUsuario
    
    # Verify order exists
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Check permissions for waiters
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para modificar este pedido"
        )
    
    # Check if order is not already delivered or canceled
    if db_pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar un pedido entregado o cancelado"
        )
    
    # Verify product exists and is available
    db_producto = db.query(Producto).filter(
        Producto.id == detalle.producto_id,
        Producto.disponible == True
    ).first()
    
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado o no disponible")
    
    # Create order detail
    subtotal = db_producto.precio * detalle.cantidad
    db_detalle = DetallePedido(
        pedido_id=pedido_id,
        producto_id=detalle.producto_id,
        cantidad=detalle.cantidad,
        precio_unitario=db_producto.precio,
        subtotal=subtotal,
        observaciones=detalle.observaciones
    )
    db.add(db_detalle)
    
    # Update order total
    db_pedido.total += subtotal
    
    # Update order update timestamp
    db_pedido.fecha_actualizacion = datetime.now(UTC)
    
    db.commit()
    db.refresh(db_detalle)
    
    # Notify kitchen about new detail
    mensaje = {
        "tipo": "nuevo_detalle",
        "pedido_id": db_pedido.id,
        "detalle_id": db_detalle.id,
        "producto": db_producto.nombre,
        "cantidad": detalle.cantidad,
        "mesa": db_pedido.mesa.numero,
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "cocina")
    
    return db_detalle

def delete_detalle_pedido(
    db: Session, 
    pedido_id: int, 
    detalle_id: int, 
    current_user: Usuario
) -> None:
    """Delete an order detail"""
    from app.core.enums import RolUsuario
    
    # Verify order exists
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Check permissions for waiters
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para modificar este pedido"
        )
    
    # Check if order is not already delivered or canceled
    if db_pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar un pedido entregado o cancelado"
        )
    
    # Verify order detail exists and belongs to order
    db_detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    
    if db_detalle is None:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    
    # Check if it's not the last detail in the order
    cantidad_detalles = db.query(DetallePedido).filter(
        DetallePedido.pedido_id == pedido_id
    ).count()
    
    if cantidad_detalles <= 1:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el último producto del pedido. Cancele el pedido completo."
        )
    
    # Update order total
    db_pedido.total -= db_detalle.subtotal
    
    # Save info for notification
    producto_nombre = db_detalle.producto.nombre
    mesa_numero = db_pedido.mesa.numero
    
    # Delete detail
    db.delete(db_detalle)
    
    # Update order update timestamp
    db_pedido.fecha_actualizacion = datetime.now(UTC)
    
    db.commit()
    
    # Notify kitchen about deleted detail
    mensaje = {
        "tipo": "eliminar_detalle",
        "pedido_id": pedido_id,
        "detalle_id": detalle_id,
        "producto": producto_nombre,
        "mesa": mesa_numero,
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "cocina") 