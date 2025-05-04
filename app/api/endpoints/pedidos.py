"""
Order management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.pedido import (
    PedidoCreate, PedidoUpdate, PedidoResponse, PedidoDetallado,
    DetallePedidoCreate, DetallePedidoUpdate, DetallePedidoResponse
)
from app.services import pedido_service
from app.api.dependencies.auth import get_usuario_actual, get_camarero_actual, get_cocinero_actual
from app.core.enums import EstadoPedido

router = APIRouter(
    prefix="/pedidos",
    tags=["pedidos"],
    dependencies=[Depends(get_usuario_actual)]
)

@router.post("/", response_model=PedidoDetallado, status_code=status.HTTP_201_CREATED)
def create_pedido(
    pedido: PedidoCreate,
    db: Session = Depends(get_db),
    camarero: Usuario = Depends(get_camarero_actual)
):
    """
    Create a new order with details. (Waiters/Admins only)
    """
    return pedido_service.create_pedido(db=db, pedido=pedido, camarero_id=camarero.id)

@router.get("/", response_model=List[PedidoResponse])
def read_pedidos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[EstadoPedido] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    mesa_id: Optional[int] = None,
    camarero_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Get all orders with optional filters.
    - Waiters can only see their own orders
    - Admins can see all orders or filter by waiter
    - Cooks can see all orders
    """
    return pedido_service.get_pedidos(
        db, 
        skip=skip, 
        limit=limit,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mesa_id=mesa_id,
        camarero_id=camarero_id,
        current_user=current_user
    )

@router.get("/{pedido_id}", response_model=PedidoDetallado)
def read_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Get a specific order by ID with all its details.
    - Waiters can only see their own orders
    - Admins and Cooks can see any order
    """
    return pedido_service.get_pedido_by_id(db, pedido_id=pedido_id, current_user=current_user)

@router.put("/{pedido_id}", response_model=PedidoResponse)
def update_pedido(
    pedido_id: int,
    pedido: PedidoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Update an order's status or observations.
    - Waiters can only update their own orders
    - Cooks can only change status to 'en_preparacion' or 'listo'
    - Admins can update any order
    """
    return pedido_service.update_pedido(
        db=db, 
        pedido_id=pedido_id, 
        pedido=pedido, 
        current_user=current_user
    )

@router.post("/{pedido_id}/detalles/", response_model=DetallePedidoResponse, status_code=status.HTTP_201_CREATED)
def create_detalle_pedido(
    pedido_id: int,
    detalle: DetallePedidoCreate,
    db: Session = Depends(get_db),
    camarero: Usuario = Depends(get_camarero_actual)
):
    """
    Add a new item to an existing order. (Waiters/Admins only)
    """
    return pedido_service.create_detalle_pedido(
        db=db, 
        pedido_id=pedido_id, 
        detalle=detalle, 
        current_user=camarero
    )

@router.put("/{pedido_id}/detalles/{detalle_id}", response_model=DetallePedidoResponse)
def update_detalle_pedido(
    pedido_id: int,
    detalle_id: int,
    detalle: DetallePedidoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Update an order detail.
    - Waiters can modify quantity and observations
    - Cooks can only change status to 'en_preparacion' or 'listo'
    - Admins can update any detail
    """
    return pedido_service.update_detalle_pedido(
        db=db, 
        pedido_id=pedido_id, 
        detalle_id=detalle_id, 
        detalle=detalle, 
        current_user=current_user
    )

@router.delete("/{pedido_id}/detalles/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_detalle_pedido(
    pedido_id: int,
    detalle_id: int,
    db: Session = Depends(get_db),
    camarero: Usuario = Depends(get_camarero_actual)
):
    """
    Delete an item from an order. (Waiters/Admins only)
    """
    pedido_service.delete_detalle_pedido(
        db=db, 
        pedido_id=pedido_id, 
        detalle_id=detalle_id, 
        current_user=camarero
    )
    return {} 