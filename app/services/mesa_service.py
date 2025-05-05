"""
Servicio para operaciones de Mesa.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from app.models.mesa import Mesa
from app.models.usuario import Usuario
from app.models.pedido import Pedido
from app.models.reserva import Reserva
from app.schemas.mesa import MesaCreate, MesaUpdate
from app.core.enums import EstadoMesa, EstadoPedido, EstadoReserva, RolUsuario
from app.core.websockets import log_event, safe_broadcast
from app.services.cuenta_service import generar_cuenta_desde_pedidos, create_cuenta
from app.schemas.cuenta import CuentaCreate, DetalleCuentaItem

def get_mesas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    estado: Optional[EstadoMesa] = None
) -> List[Mesa]:
    """Obtener todas las mesas con filtro opcional por estado"""
    query = db.query(Mesa)
    
    if estado is not None:
        query = query.filter(Mesa.estado == estado)
    
    return query.offset(skip).limit(limit).all()

def get_mesa_by_id(db: Session, mesa_id: int) -> Mesa:
    """Obtener una mesa específica por ID"""
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if mesa is None:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return mesa

def get_mesa_by_numero(db: Session, numero: int) -> Optional[Mesa]:
    """Obtener una mesa específica por número"""
    return db.query(Mesa).filter(Mesa.numero == numero).first()

def create_mesa(db: Session, mesa: MesaCreate, current_user: Usuario) -> Mesa:
    """Crear una nueva mesa"""
    # Solo administradores pueden crear mesas
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden crear mesas"
        )
    
    # Verificar si ya existe una mesa con el mismo número
    existing_mesa = db.query(Mesa).filter(Mesa.numero == mesa.numero).first()
    if existing_mesa:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe una mesa con el número {mesa.numero}"
        )
    
    db_mesa = Mesa(
        numero=mesa.numero,
        capacidad=mesa.capacidad,
        estado=EstadoMesa.LIBRE,
        ubicacion=mesa.ubicacion
    )
    
    db.add(db_mesa)
    db.commit()
    db.refresh(db_mesa)
    
    return db_mesa

def update_mesa(db: Session, mesa_id: int, mesa: MesaUpdate, current_user: Usuario) -> Mesa:
    """Actualizar una mesa existente"""
    db_mesa = get_mesa_by_id(db, mesa_id)
    
    # Definir permisos por rol
    if current_user.rol == RolUsuario.ADMIN:
        # Los administradores pueden cambiar todos los campos
        if mesa.capacidad is not None:
            db_mesa.capacidad = mesa.capacidad
        
        if mesa.estado is not None:
            old_estado = db_mesa.estado
            db_mesa.estado = mesa.estado
            
            # Si la mesa pasa de ocupada a libre, registrar una cuenta
            if old_estado == EstadoMesa.OCUPADA and mesa.estado == EstadoMesa.LIBRE:
                try:
                    print(f"Cerrando mesa {mesa_id}: generando cuenta final...")
                    # Generar datos para la cuenta
                    datos_cuenta = generar_cuenta_desde_pedidos(
                        db=db,
                        mesa_id=mesa_id,
                        camarero_id=current_user.id
                    )
                    
                    # Crear ítems de detalle
                    detalles = []
                    if datos_cuenta.get("detalles"):
                        for item in datos_cuenta["detalles"]:
                            detalle = DetalleCuentaItem(
                                pedido_id=item["pedido_id"],
                                producto_id=item["producto_id"],
                                nombre_producto=item["nombre_producto"],
                                cantidad=item["cantidad"],
                                precio_unitario=item["precio_unitario"],
                                subtotal=item["subtotal"],
                                observaciones=item.get("observaciones")
                            )
                            detalles.append(detalle)
                    
                    # Crear la cuenta
                    if datos_cuenta["total"] > 0:
                        cuenta_create = CuentaCreate(
                            mesa_id=mesa_id,
                            numero_mesa=datos_cuenta["numero_mesa"],
                            nombre_camarero=datos_cuenta["nombre_camarero"],
                            total=datos_cuenta["total"],
                            metodo_pago=mesa.metodo_pago,
                            detalles=detalles
                        )
                        
                        create_cuenta(
                            db=db,
                            cuenta=cuenta_create,
                            camarero_id=current_user.id
                        )
                        print(f"Cuenta creada para mesa {mesa_id} con total {datos_cuenta['total']}")
                    else:
                        print(f"No se creó cuenta para mesa {mesa_id} porque el total es 0")
                    
                    # Desvincular los pedidos de la mesa para que no aparezcan en futuras cuentas
                    pedidos = db.query(Pedido).filter(
                        Pedido.mesa_id == mesa_id,
                        Pedido.estado != EstadoPedido.CANCELADO
                    ).all()
                    
                    for pedido in pedidos:
                        pedido.estado = EstadoPedido.ENTREGADO
                        pedido.mesa_id = None  # Desvincular el pedido de la mesa
                        print(f"Pedido {pedido.id} marcado como entregado y desvinculado")
                    
                except Exception as e:
                    # No fallamos si hay error al crear la cuenta, solo lo registramos
                    print(f"Error al crear cuenta para mesa {mesa_id}: {str(e)}")
                    # Registrar error detalladamente
                    import traceback
                    print(traceback.format_exc())
        
        if mesa.ubicacion is not None:
            db_mesa.ubicacion = mesa.ubicacion
            
    elif current_user.rol == RolUsuario.CAMARERO:
        # Los camareros solo pueden cambiar el estado
        if mesa.estado is not None:
            old_estado = db_mesa.estado
            db_mesa.estado = mesa.estado
            
            # Si la mesa pasa de ocupada a libre, registrar una cuenta
            if old_estado == EstadoMesa.OCUPADA and mesa.estado == EstadoMesa.LIBRE:
                try:
                    print(f"Cerrando mesa {mesa_id}: generando cuenta final...")
                    # Generar datos para la cuenta
                    datos_cuenta = generar_cuenta_desde_pedidos(
                        db=db,
                        mesa_id=mesa_id,
                        camarero_id=current_user.id
                    )
                    
                    # Crear ítems de detalle
                    detalles = []
                    if datos_cuenta.get("detalles"):
                        for item in datos_cuenta["detalles"]:
                            detalle = DetalleCuentaItem(
                                pedido_id=item["pedido_id"],
                                producto_id=item["producto_id"],
                                nombre_producto=item["nombre_producto"],
                                cantidad=item["cantidad"],
                                precio_unitario=item["precio_unitario"],
                                subtotal=item["subtotal"],
                                observaciones=item.get("observaciones")
                            )
                            detalles.append(detalle)
                    
                    # Crear la cuenta
                    if datos_cuenta["total"] > 0:
                        cuenta_create = CuentaCreate(
                            mesa_id=mesa_id,
                            numero_mesa=datos_cuenta["numero_mesa"],
                            nombre_camarero=datos_cuenta["nombre_camarero"],
                            total=datos_cuenta["total"],
                            metodo_pago=mesa.metodo_pago,
                            detalles=detalles
                        )
                        
                        create_cuenta(
                            db=db,
                            cuenta=cuenta_create,
                            camarero_id=current_user.id
                        )
                        print(f"Cuenta creada para mesa {mesa_id} con total {datos_cuenta['total']}")
                    else:
                        print(f"No se creó cuenta para mesa {mesa_id} porque el total es 0")
                    
                    # Desvincular los pedidos de la mesa para que no aparezcan en futuras cuentas
                    pedidos = db.query(Pedido).filter(
                        Pedido.mesa_id == mesa_id,
                        Pedido.estado != EstadoPedido.CANCELADO
                    ).all()
                    
                    for pedido in pedidos:
                        pedido.estado = EstadoPedido.ENTREGADO
                        pedido.mesa_id = None  # Desvincular el pedido de la mesa
                        print(f"Pedido {pedido.id} marcado como entregado y desvinculado")
                    
                except Exception as e:
                    # No fallamos si hay error al crear la cuenta, solo lo registramos
                    print(f"Error al crear cuenta para mesa {mesa_id}: {str(e)}")
                    # Registrar error detalladamente
                    import traceback
                    print(traceback.format_exc())
    else:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para actualizar mesas"
        )
    
    db.commit()
    db.refresh(db_mesa)
    
    return db_mesa

def delete_mesa(db: Session, mesa_id: int, current_user: Usuario) -> None:
    """Eliminar una mesa"""
    # Solo administradores pueden eliminar mesas
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden eliminar mesas"
        )
    
    db_mesa = get_mesa_by_id(db, mesa_id)
    
    # Verificar que la mesa no tenga pedidos activos
    pedidos_activos = db.query(Pedido).filter(
        Pedido.mesa_id == mesa_id,
        Pedido.estado.not_in([EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO])
    ).count()
    
    if pedidos_activos > 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar una mesa con pedidos activos"
        )
    
    db.delete(db_mesa)
    db.commit()
    
    return None