"""
Service for Mesa operations.
"""
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from app.models.mesa import Mesa
from app.models.pedido import Pedido
from app.models.reserva import Reserva
from app.schemas.mesa import MesaCreate, MesaUpdate
from app.core.enums import EstadoMesa, EstadoPedido, EstadoReserva
from app.core.websockets import log_event, safe_broadcast

def get_mesas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    estado: Optional[EstadoMesa] = None
) -> List[Mesa]:
    """Get tables with optional filters"""
    query = db.query(Mesa)
    
    if estado is not None:
        query = query.filter(Mesa.estado == estado)
    
    return query.offset(skip).limit(limit).all()

def get_mesa_by_id(db: Session, mesa_id: int) -> Mesa:
    """Get a specific table by ID"""
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if mesa is None:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return mesa

def get_mesa_by_numero(db: Session, numero: int) -> Optional[Mesa]:
    """Get a specific table by number"""
    return db.query(Mesa).filter(Mesa.numero == numero).first()

def create_mesa(db: Session, mesa: MesaCreate) -> Mesa:
    """Create a new table"""
    # Check if table number already exists
    db_mesa = get_mesa_by_numero(db, mesa.numero)
    if db_mesa:
        raise HTTPException(status_code=400, detail="El número de mesa ya existe")
    
    # Create table
    db_mesa = Mesa(**mesa.model_dump())
    db.add(db_mesa)
    db.commit()
    db.refresh(db_mesa)
    return db_mesa

def update_mesa(db: Session, mesa_id: int, mesa: MesaUpdate) -> Mesa:
    """Update a table"""
    db_mesa = get_mesa_by_id(db, mesa_id)
    
    # Update fields
    for key, value in mesa.model_dump(exclude_unset=True).items():
        setattr(db_mesa, key, value)
    
    db.commit()
    db.refresh(db_mesa)
    return db_mesa

def delete_mesa(db: Session, mesa_id: int) -> None:
    """Delete a table"""
    db_mesa = get_mesa_by_id(db, mesa_id)
    
    # Check if table has active orders
    pedidos_activos = db.query(Pedido).filter(
        Pedido.mesa_id == mesa_id,
        Pedido.estado.in_([EstadoPedido.RECIBIDO, EstadoPedido.EN_PREPARACION])
    ).count()
    
    if pedidos_activos > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la mesa porque tiene {pedidos_activos} pedidos activos"
        )
    
    # Check if table has future reservations
    reservas_futuras = db.query(Reserva).filter(
        Reserva.mesa_id == mesa_id,
        Reserva.fecha > datetime.now(UTC),
        Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA])
    ).count()
    
    if reservas_futuras > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la mesa porque tiene {reservas_futuras} reservas futuras"
        )
    
    # Delete table
    db.delete(db_mesa)
    db.commit()