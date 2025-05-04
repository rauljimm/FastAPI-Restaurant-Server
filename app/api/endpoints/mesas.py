"""
Table management endpoints.
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
    Create a new table. (Admin only)
    """
    return mesa_service.create_mesa(db=db, mesa=mesa)

@router.get("/", response_model=List[MesaResponse])
def read_mesas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[EstadoMesa] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Get all tables with optional filters.
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
    Get a specific table by ID.
    """
    return mesa_service.get_mesa_by_id(db, mesa_id=mesa_id)

@router.put("/{mesa_id}", response_model=MesaResponse)
def update_mesa(
    mesa_id: int,
    mesa: MesaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Update a table.
    - Admins can perform any update
    - Waiters can change the status of tables to any value
    """
    # Si es admin o camarero, puede realizar cualquier actualización de estado
    if current_user.rol == RolUsuario.ADMIN or current_user.rol == RolUsuario.CAMARERO:
        # Registrar la acción en el log
        from app.core.websockets import log_event
        log_event(f"Usuario {current_user.username} [{current_user.rol}] está cambiando el estado de la mesa {mesa_id} a '{mesa.estado}'", "info")
        
        return mesa_service.update_mesa(db=db, mesa_id=mesa_id, mesa=mesa)
    
    # Cualquier otro rol no tiene permisos
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción"
        )

@router.delete("/{mesa_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_mesa(
    mesa_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Delete a table. (Admin only)
    """
    mesa_service.delete_mesa(db=db, mesa_id=mesa_id)
    return {} 