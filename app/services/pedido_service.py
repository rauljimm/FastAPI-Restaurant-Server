"""
Servicio para operaciones de Pedido.
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
    """Obtener pedidos con filtros opcionales"""
    query = db.query(Pedido)
    
    # Aplicar filtros
    if estado is not None:
        query = query.filter(Pedido.estado == estado)
    
    if fecha_inicio is not None:
        query = query.filter(Pedido.fecha_creacion >= fecha_inicio)
    
    if fecha_fin is not None:
        query = query.filter(Pedido.fecha_creacion <= fecha_fin)
    
    if mesa_id is not None:
        query = query.filter(Pedido.mesa_id == mesa_id)
    
    # Aplicar filtrado por usuario
    if current_user is not None:
        from app.core.enums import RolUsuario
        
        if current_user.rol == RolUsuario.CAMARERO:
            # Los camareros solo pueden ver sus propios pedidos
            query = query.filter(Pedido.camarero_id == current_user.id)
        elif current_user.rol == RolUsuario.ADMIN and camarero_id is not None:
            # Los administradores pueden filtrar por camarero específico
            query = query.filter(Pedido.camarero_id == camarero_id)
    
    # Ordenar por fecha de creación (últimos primero)
    query = query.order_by(Pedido.fecha_creacion.desc())
    
    return query.offset(skip).limit(limit).all()

def get_pedido_by_id(db: Session, pedido_id: int, current_user: Usuario = None) -> Pedido:
    """Obtener un pedido específico por ID"""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar permisos
    if current_user is not None:
        from app.core.enums import RolUsuario
        
        if current_user.rol == RolUsuario.CAMARERO and pedido.camarero_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para ver este pedido"
            )
    
    return pedido

def create_pedido(db: Session, pedido: PedidoCreate, camarero_id: int) -> Pedido:
    """Crear un nuevo pedido"""
    # Verificar si la mesa existe
    mesa = db.query(Mesa).filter(Mesa.id == pedido.mesa_id).first()
    if mesa is None:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    
    # Verificar si la mesa está disponible
    if mesa.estado not in [EstadoMesa.LIBRE, EstadoMesa.OCUPADA]:
        raise HTTPException(status_code=400, detail="La mesa no está disponible")
    
    # Verificar si el pedido tiene productos
    if not pedido.detalles:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos un producto")
    
    # Crear pedido
    db_pedido = Pedido(
        mesa_id=pedido.mesa_id,
        camarero_id=camarero_id,
        observaciones=pedido.observaciones
    )
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    
    # Establecer la mesa como ocupada
    mesa.estado = EstadoMesa.OCUPADA
    db.commit()
    
    # Agregar detalles del pedido
    total_pedido = 0.0
    for detalle in pedido.detalles:
        db_producto = db.query(Producto).filter(
            Producto.id == detalle.producto_id,
            Producto.disponible == True
        ).first()
        
        if db_producto is None:
            # Si el producto no existe o no está disponible, eliminar el pedido
            db.delete(db_pedido)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Producto {detalle.producto_id} no encontrado o no disponible")
        
        # Crear detalle del pedido
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
    
    # Actualizar total del pedido
    db_pedido.total = total_pedido
    db.commit()
    db.refresh(db_pedido)
    
    # Notificar a la cocina sobre el nuevo pedido
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
    """Actualizar un pedido"""
    from app.core.enums import RolUsuario
    
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Verificar permisos para camareros
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para actualizar este pedido"
        )
    
    # Los cocineros solo pueden cambiar el estado a 'en_preparacion' o 'listo'
    if current_user.rol == RolUsuario.COCINERO:
        if pedido.estado not in [EstadoPedido.EN_PREPARACION, EstadoPedido.LISTO]:
            raise HTTPException(
                status_code=403,
                detail="Los cocineros solo pueden cambiar el estado a 'en_preparacion' o 'listo'"
            )
    
    # Actualizar campos
    for key, value in pedido.model_dump(exclude_unset=True).items():
        setattr(db_pedido, key, value)
    
    db.commit()
    db.refresh(db_pedido)
    
    # Notificar sobre la actualización del pedido
    mensaje = {
        "tipo": "actualizacion_pedido",
        "pedido_id": db_pedido.id,
        "estado": db_pedido.estado,
        "mesa": db_pedido.mesa.numero,
        "hora": datetime.now(UTC).isoformat()
    }
    
    if current_user.rol == RolUsuario.COCINERO:
        # Si el cocinero cambia el estado, notificar a los camareros
        safe_broadcast(mensaje, "camareros")
    else:
        # Si el camarero o el administrador cambia el estado, notificar a la cocina
        safe_broadcast(mensaje, "cocina")
    
    return db_pedido

def update_detalle_pedido(
    db: Session, 
    pedido_id: int, 
    detalle_id: int, 
    detalle: DetallePedidoUpdate, 
    current_user: Usuario
) -> DetallePedido:
    """Actualizar un detalle del pedido"""
    from app.core.enums import RolUsuario
    
    # Verificar si el pedido existe
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Verificar permisos para camareros
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para actualizar este pedido"
        )
    
    # Verificar si el pedido no está ya entregado o cancelado
    if db_pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar un pedido entregado o cancelado"
        )
    
    # Verificar si el detalle del pedido existe y pertenece al pedido
    db_detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    
    if db_detalle is None:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    
    # Los cocineros solo pueden cambiar el estado
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
        # Los camareros y los administradores pueden actualizar todo
        if detalle.cantidad is not None:
            if detalle.cantidad <= 0:
                raise HTTPException(status_code=400, detail="La cantidad debe ser mayor que cero")
            
            # Recalcular el subtotal
            db_detalle.cantidad = detalle.cantidad
            db_detalle.subtotal = db_detalle.precio_unitario * detalle.cantidad
            
            # Actualizar total del pedido
            nuevo_total = db.query(func.sum(DetallePedido.subtotal)).filter(
                DetallePedido.pedido_id == pedido_id
            ).scalar() or 0.0
            
            db_pedido.total = nuevo_total
        
        if detalle.estado is not None:
            db_detalle.estado = detalle.estado
        
        if detalle.observaciones is not None:
            db_detalle.observaciones = detalle.observaciones
    
    # Actualizar la marca de tiempo de actualización del pedido
    db_pedido.fecha_actualizacion = datetime.now(UTC)
    
    db.commit()
    db.refresh(db_detalle)
    
    # Notificar sobre la actualización del detalle
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
    """Agregar un nuevo detalle a un pedido existente"""
    from app.core.enums import RolUsuario
    
    # Verificar si el pedido existe
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Verificar permisos para camareros
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para modificar este pedido"
        )
    
    # Verificar si el pedido no está ya entregado o cancelado
    if db_pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar un pedido entregado o cancelado"
        )
    
    # Verificar si el producto existe y está disponible
    db_producto = db.query(Producto).filter(
        Producto.id == detalle.producto_id,
        Producto.disponible == True
    ).first()
    
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado o no disponible")
    
    # Crear detalle del pedido
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
    
    # Actualizar total del pedido
    db_pedido.total += subtotal
    
    # Actualizar la marca de tiempo de actualización del pedido
    db_pedido.fecha_actualizacion = datetime.now(UTC)
    
    db.commit()
    db.refresh(db_detalle)
    
    # Notificar a la cocina sobre el nuevo detalle
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
    """Eliminar un detalle del pedido"""
    from app.core.enums import RolUsuario
    
    # Verificar si el pedido existe
    db_pedido = get_pedido_by_id(db, pedido_id, current_user)
    
    # Verificar permisos para camareros
    if current_user.rol == RolUsuario.CAMARERO and db_pedido.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para modificar este pedido"
        )
    
    # Verificar si el pedido no está ya entregado o cancelado
    if db_pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
        raise HTTPException(
            status_code=400,
            detail="No se puede modificar un pedido entregado o cancelado"
        )
    
    # Verificar si el detalle del pedido existe y pertenece al pedido
    db_detalle = db.query(DetallePedido).filter(
        DetallePedido.id == detalle_id,
        DetallePedido.pedido_id == pedido_id
    ).first()
    
    if db_detalle is None:
        raise HTTPException(status_code=404, detail="Detalle de pedido no encontrado")
    
    # Verificar si no es el último detalle en el pedido
    cantidad_detalles = db.query(DetallePedido).filter(
        DetallePedido.pedido_id == pedido_id
    ).count()
    
    if cantidad_detalles <= 1:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el último producto del pedido. Cancele el pedido completo."
        )
    
    # Actualizar total del pedido
    db_pedido.total -= db_detalle.subtotal
    
    # Guardar información para la notificación
    producto_nombre = db_detalle.producto.nombre
    mesa_numero = db_pedido.mesa.numero
    
    # Eliminar detalle
    db.delete(db_detalle)
    
    # Actualizar la marca de tiempo de actualización del pedido
    db_pedido.fecha_actualizacion = datetime.now(UTC)
    
    db.commit()
    
    # Notificar a la cocina sobre la eliminación del detalle
    mensaje = {
        "tipo": "eliminar_detalle",
        "pedido_id": pedido_id,
        "detalle_id": detalle_id,
        "producto": producto_nombre,
        "mesa": mesa_numero,
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "cocina") 