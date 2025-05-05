"""
Endpoints de gestión de pedidos.
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
    Crear un nuevo pedido con detalles. (Camareros/Administradores solo)
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
    activos: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener todos los pedidos con filtros opcionales.
    - Los camareros solo pueden ver sus propios pedidos
    - Los administradores pueden ver todos los pedidos o filtrar por camarero
    - Los cocineros pueden ver todos los pedidos
    - Si activos=True, solo se muestran pedidos en estado distinto a ENTREGADO y CANCELADO
    """
    if activos is True:
        estados_activos = [estado for estado in EstadoPedido if estado not in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]]
        if estado is not None and estado not in estados_activos:
            return []
        elif estado is None:
            estado = None
    
    pedidos = pedido_service.get_pedidos(
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
    
    if activos is True and estado is None:
        pedidos = [p for p in pedidos if p.estado not in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]]
    
    return pedidos

@router.get("/{pedido_id}", response_model=PedidoDetallado)
def read_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener un pedido específico por ID con todos sus detalles.
    - Los camareros solo pueden ver sus propios pedidos
    - Los administradores y cocineros pueden ver cualquier pedido
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
    Actualizar el estado o observaciones de un pedido.
    - Los camareros solo pueden actualizar sus propios pedidos
    - Los cocineros solo pueden cambiar el estado a 'en_preparacion' o 'listo'
    - Los administradores pueden actualizar cualquier pedido
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
    Añadir un nuevo elemento a un pedido existente. (Camareros/Administradores solo)
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
    Actualizar un detalle de un pedido.
    - Los camareros pueden modificar la cantidad y observaciones
    - Los cocineros solo pueden cambiar el estado a 'en_preparacion' o 'listo'
    - Los administradores pueden actualizar cualquier detalle
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
    Eliminar un elemento de un pedido. (Camareros/Administradores solo)
    """
    pedido_service.delete_detalle_pedido(
        db=db, 
        pedido_id=pedido_id, 
        detalle_id=detalle_id, 
        current_user=camarero
    )
    return {} 