"""
Servicio para operaciones de Reserva.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from app.models.reserva import Reserva
from app.models.mesa import Mesa
from app.schemas.reserva import ReservaCreate, ReservaUpdate
from app.core.enums import EstadoReserva, EstadoMesa
from app.core.websockets import safe_broadcast

def get_reservas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    estado: Optional[EstadoReserva] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    mesa_id: Optional[int] = None
) -> List[Reserva]:
    """Obtener reservas con filtros opcionales"""
    query = db.query(Reserva)
    
    if estado is not None:
        query = query.filter(Reserva.estado == estado)
    
    if fecha_inicio is not None:
        query = query.filter(Reserva.fecha >= fecha_inicio)
    
    if fecha_fin is not None:
        query = query.filter(Reserva.fecha <= fecha_fin)
    
    if mesa_id is not None:
        query = query.filter(Reserva.mesa_id == mesa_id)
    
    # Order by date (newest first)
    query = query.order_by(Reserva.fecha.desc())
    
    return query.offset(skip).limit(limit).all()

def get_reserva_by_id(db: Session, reserva_id: int) -> Reserva:
    """Obtener una reserva específica por ID"""
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if reserva is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva

def create_reserva(db: Session, reserva: ReservaCreate) -> Reserva:
    """Crear una nueva reserva"""
    # Verificar si la fecha de reserva es en el futuro
    if reserva.fecha <= datetime.now(UTC):
        raise HTTPException(
            status_code=400,
            detail="La fecha de reserva debe ser en el futuro"
        )
    
    # Verificar si el número de personas es válido
    if reserva.num_personas <= 0:
        raise HTTPException(
            status_code=400,
            detail="El número de personas debe ser mayor que cero"
        )
    
    # Verificar si la duración es válida
    if reserva.duracion and reserva.duracion <= 0:
        raise HTTPException(
            status_code=400,
            detail="La duración debe ser mayor que cero"
        )
    
    # Si se especifica una mesa, verificar si existe y está disponible
    if reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == reserva.mesa_id).first()
        if mesa is None:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        
        # Verificar la capacidad de la mesa
        if mesa.capacidad < reserva.num_personas:
            raise HTTPException(
                status_code=400,
                detail="La mesa no tiene suficiente capacidad para el número de personas"
            )
        
        # Verificar la disponibilidad de la mesa para el horario solicitado
        fecha_fin = reserva.fecha + timedelta(minutes=reserva.duracion or 120)
        reservas_conflictivas = db.query(Reserva).filter(
            Reserva.mesa_id == reserva.mesa_id,
            Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]),
            Reserva.fecha < fecha_fin,
            Reserva.fecha + timedelta(minutes=120) > reserva.fecha
        ).count()
        
        if reservas_conflictivas > 0:
            raise HTTPException(
                status_code=400,
                detail="La mesa ya está reservada en el horario solicitado"
            )
    
    # Crear reserva
    db_reserva = Reserva(**reserva.model_dump())
    db.add(db_reserva)
    db.commit()
    db.refresh(db_reserva)
    
    # Actualizar el estado de la mesa si se asigna
    if reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == reserva.mesa_id).first()
        mesa.estado = EstadoMesa.RESERVADA
        db.commit()
    
    # Notificar a los administradores sobre la nueva reserva
    if reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == reserva.mesa_id).first()
        mesa_numero = mesa.numero
    else:
        mesa_numero = None
    
    mensaje = {
        "tipo": "nueva_reserva",
        "reserva_id": db_reserva.id,
        "cliente": f"{reserva.cliente_nombre} {reserva.cliente_apellido}",
        "fecha": reserva.fecha.isoformat(),
        "mesa": mesa_numero,
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "admin")
    
    return db_reserva

def update_reserva(db: Session, reserva_id: int, reserva: ReservaUpdate) -> Reserva:
    """Actualizar una reserva"""
    db_reserva = get_reserva_by_id(db, reserva_id)
    
    # Verificar si la nueva fecha es en el futuro
    if reserva.fecha is not None and reserva.fecha <= datetime.now(UTC):
        raise HTTPException(
            status_code=400,
            detail="La fecha de reserva debe ser en el futuro"
        )
    
    # Verificar si la mesa está cambiando
    mesa_anterior_id = db_reserva.mesa_id
    if reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == reserva.mesa_id).first()
        if mesa is None:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        
        # Verificar la capacidad
        num_personas = reserva.num_personas if reserva.num_personas is not None else db_reserva.num_personas
        if mesa.capacidad < num_personas:
            raise HTTPException(
                status_code=400,
                detail="La mesa no tiene suficiente capacidad"
            )
        
        # Verificar la disponibilidad
        fecha = reserva.fecha if reserva.fecha is not None else db_reserva.fecha
        duracion = reserva.duracion if reserva.duracion is not None else db_reserva.duracion
        fecha_fin = fecha + timedelta(minutes=duracion)
        reservas_conflictivas = db.query(Reserva).filter(
            Reserva.mesa_id == reserva.mesa_id,
            Reserva.id != reserva_id,
            Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]),
            Reserva.fecha < fecha_fin,
            Reserva.fecha + timedelta(minutes=120) > fecha
        ).count()
        
        if reservas_conflictivas > 0:
            raise HTTPException(
                status_code=400,
                detail="La mesa ya está reservada en el horario solicitado"
            )
    
    # Actualizar campos
    for key, value in reserva.model_dump(exclude_unset=True).items():
        setattr(db_reserva, key, value)
    
    # Actualizar el estado de la mesa si es necesario
    if reserva.mesa_id is not None and reserva.mesa_id != mesa_anterior_id:
        # Actualizar la nueva mesa
        mesa = db.query(Mesa).filter(Mesa.id == reserva.mesa_id).first()
        mesa.estado = EstadoMesa.RESERVADA
        
        # Liberar la mesa anterior si existía
        if mesa_anterior_id is not None:
            mesa_anterior = db.query(Mesa).filter(Mesa.id == mesa_anterior_id).first()
            # Verificar si la mesa anterior tiene otras reservas activas
            reservas_activas = db.query(Reserva).filter(
                Reserva.mesa_id == mesa_anterior_id,
                Reserva.id != reserva_id,
                Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]),
                Reserva.fecha > datetime.now(UTC)
            ).count()
            if reservas_activas == 0:
                mesa_anterior.estado = EstadoMesa.LIBRE
    
    # Si la reserva está cancelada, completada o el cliente no llegó, liberar la mesa
    if reserva.estado in [EstadoReserva.CANCELADA, EstadoReserva.COMPLETADA, EstadoReserva.CLIENTE_NO_LLEGO] and db_reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == db_reserva.mesa_id).first()
        reservas_activas = db.query(Reserva).filter(
            Reserva.mesa_id == db_reserva.mesa_id,
            Reserva.id != reserva_id,
            Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]),
            Reserva.fecha > datetime.now(UTC)
        ).count()
        if reservas_activas == 0:
            mesa.estado = EstadoMesa.LIBRE
    
    # Si el cliente llegó, cambiamos el estado de la mesa a ocupada
    if reserva.estado == EstadoReserva.CLIENTE_LLEGO and db_reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == db_reserva.mesa_id).first()
        mesa.estado = EstadoMesa.OCUPADA
    
    db.commit()
    db.refresh(db_reserva)
    
    # Notificar a los administradores sobre la actualización
    mesa_numero = None
    if db_reserva.mesa_id:
        mesa = db.query(Mesa).filter(Mesa.id == db_reserva.mesa_id).first()
        mesa_numero = mesa.numero
        
    mensaje = {
        "tipo": "actualizacion_reserva",
        "reserva_id": db_reserva.id,
        "estado": db_reserva.estado,
        "cliente": f"{db_reserva.cliente_nombre} {db_reserva.cliente_apellido}",
        "fecha": db_reserva.fecha.isoformat(),
        "mesa": mesa_numero,
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "admin")
    
    return db_reserva

def delete_reserva(db: Session, reserva_id: int) -> None:
    """Eliminar una reserva"""
    db_reserva = get_reserva_by_id(db, reserva_id)
    
    # Liberar la mesa si está asignada
    if db_reserva.mesa_id is not None:
        mesa = db.query(Mesa).filter(Mesa.id == db_reserva.mesa_id).first()
        reservas_activas = db.query(Reserva).filter(
            Reserva.mesa_id == db_reserva.mesa_id,
            Reserva.id != reserva_id,
            Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]),
            Reserva.fecha > datetime.now(UTC)
        ).count()
        if reservas_activas == 0:
            mesa.estado = EstadoMesa.LIBRE
    
    # Guardar información para la notificación
    cliente = f"{db_reserva.cliente_nombre} {db_reserva.cliente_apellido}"
    fecha = db_reserva.fecha.isoformat()
    mesa_numero = None
    if db_reserva.mesa_id:
        mesa_numero = mesa.numero
    
    db.delete(db_reserva)
    db.commit()
    
    # Notificar a los administradores sobre la eliminación
    mensaje = {
        "tipo": "eliminar_reserva",
        "reserva_id": reserva_id,
        "cliente": cliente,
        "fecha": fecha,
        "mesa": mesa_numero,
        "hora": datetime.now(UTC).isoformat()
    }
    safe_broadcast(mensaje, "admin") 