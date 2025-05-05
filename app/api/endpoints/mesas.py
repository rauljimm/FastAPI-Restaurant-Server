"""
Endpoints de gestión de mesas.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.mesa import MesaCreate, MesaUpdate, MesaResponse
from app.services import mesa_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual, get_camarero_actual
from app.core.enums import EstadoMesa, RolUsuario
from app.models.reserva import Reserva
from app.core.enums import EstadoReserva
from app.schemas.reserva import ReservaResponse

router = APIRouter(
    prefix="/mesas",
    tags=["mesas"],
    dependencies=[Depends(get_usuario_actual)]
)

@router.post("/", response_model=MesaResponse, status_code=status.HTTP_201_CREATED)
def create_mesa(
    mesa: MesaCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Crear una nueva mesa. (Administradores)
    """
    return mesa_service.create_mesa(db=db, mesa=mesa, current_user=admin)

@router.get("/", response_model=List[MesaResponse])
def read_mesas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[EstadoMesa] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener todas las mesas con filtros opcionales.
    """
    mesas = mesa_service.get_mesas(
        db, 
        skip=skip, 
        limit=limit,
        estado=estado
    )
    return mesas

@router.get("/{mesa_id}", response_model=MesaResponse)
def read_mesa(
    mesa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener detalles de una mesa específica.
    """
    return mesa_service.get_mesa_by_id(db=db, mesa_id=mesa_id)

@router.get("/{mesa_id}/reserva-activa", response_model=ReservaResponse)
def get_reserva_activa(
    mesa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener la reserva activa para una mesa específica.
    """
    from datetime import datetime, timedelta, UTC
    
    # Buscar reservas pendientes o confirmadas para esta mesa
    reservas = db.query(Reserva).filter(
        Reserva.mesa_id == mesa_id,
        Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]),
        Reserva.fecha > datetime.now(UTC) - timedelta(hours=2),  # Incluir reservas de hasta 2 horas antes
        Reserva.fecha < datetime.now(UTC) + timedelta(hours=2)   # Solo reservas recientes o próximas
    ).order_by(Reserva.fecha).first()
    
    if not reservas:
        raise HTTPException(status_code=404, detail="No hay reservas activas para esta mesa")
    
    return reservas

@router.put("/{mesa_id}", response_model=MesaResponse)
def update_mesa(
    mesa_id: int,
    mesa: MesaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Actualizar una mesa.
    - Camareros pueden cambiar el estado
    - Administradores pueden cambiar cualquier campo
    """
    return mesa_service.update_mesa(db=db, mesa_id=mesa_id, mesa=mesa, current_user=current_user)

@router.delete("/{mesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mesa(
    mesa_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Eliminar una mesa. (Administradores)
    La mesa no debe tener pedidos activos ni reservas futuras.
    """
    mesa_service.delete_mesa(db=db, mesa_id=mesa_id, current_user=admin)
    return None 