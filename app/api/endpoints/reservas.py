"""
Endpoints de gestión de reservas.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.reserva import ReservaCreate, ReservaUpdate, ReservaResponse, ReservaDetallada
from app.services import reserva_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual, get_camarero_actual
from app.core.enums import EstadoReserva

router = APIRouter(
    prefix="/reservas",
    tags=["reservas"],
    dependencies=[Depends(get_usuario_actual)]
)

@router.post("/", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
def create_reserva(
    reserva: ReservaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Crear una nueva reserva.
    """
    return reserva_service.create_reserva(db=db, reserva=reserva)

@router.get("/", response_model=List[ReservaResponse])
def read_reservas(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[EstadoReserva] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    mesa_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener todas las reservas con filtros opcionales.
    """
    return reserva_service.get_reservas(
        db, 
        skip=skip, 
        limit=limit,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mesa_id=mesa_id
    )

@router.get("/{reserva_id}", response_model=ReservaDetallada)
def read_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener una reserva específica por ID.
    """
    return reserva_service.get_reserva_by_id(db, reserva_id=reserva_id)

@router.put("/{reserva_id}", response_model=ReservaResponse)
def update_reserva(
    reserva_id: int,
    reserva: ReservaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Actualizar una reserva.
    """
    return reserva_service.update_reserva(db=db, reserva_id=reserva_id, reserva=reserva)

@router.delete("/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_camarero_actual)
):
    """
    Eliminar una reserva. (Camareros y administradores)
    """
    reserva_service.delete_reserva(db=db, reserva_id=reserva_id)
    return {} 