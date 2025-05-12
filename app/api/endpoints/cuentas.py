"""
Endpoints de gestión de cuentas.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.cuenta import CuentaCreate, CuentaUpdate, CuentaResponse
from app.services import cuenta_service
from app.api.dependencies.auth import get_usuario_actual, get_admin_actual, get_camarero_actual

router = APIRouter(
    prefix="/cuentas",
    tags=["cuentas"],
    dependencies=[Depends(get_usuario_actual)]
)

@router.post("/", response_model=CuentaResponse, status_code=status.HTTP_201_CREATED)
def create_cuenta(
    cuenta: CuentaCreate,
    db: Session = Depends(get_db),
    camarero: Usuario = Depends(get_camarero_actual)
):
    """
    Crear una nueva cuenta. (Camareros/Administradores solo)
    """
    return cuenta_service.create_cuenta(
        db=db, 
        cuenta=cuenta, 
        camarero_id=camarero.id
    )

@router.get("/", response_model=List[CuentaResponse])
def read_cuentas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    mesa_id: Optional[int] = None,
    camarero_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener todas las cuentas con filtros opcionales.
    - Los camareros solo pueden ver sus propias cuentas
    - Los administradores pueden ver todas las cuentas o filtrar por camarero
    """
    return cuenta_service.get_cuentas(
        db=db, 
        skip=skip, 
        limit=limit,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mesa_id=mesa_id,
        camarero_id=camarero_id,
        current_user=current_user
    )

@router.get("/resumen", response_model=Dict[str, Any])
def get_resumen_cuentas(
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Obtener resumen estadístico de cuentas e ingresos. (Solo Administradores)
    """
    return cuenta_service.get_resumen_cuentas(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        current_user=admin
    )

@router.get("/{cuenta_id}", response_model=CuentaResponse)
def read_cuenta(
    cuenta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Obtener una cuenta específica por ID.
    - Los camareros solo pueden ver sus propias cuentas
    - Los administradores pueden ver cualquier cuenta
    """
    return cuenta_service.get_cuenta_by_id(
        db=db, 
        cuenta_id=cuenta_id, 
        current_user=current_user
    )

@router.put("/{cuenta_id}", response_model=CuentaResponse)
def update_cuenta(
    cuenta_id: int,
    cuenta: CuentaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """
    Actualizar una cuenta existente (solo método de pago).
    - Los camareros solo pueden actualizar sus propias cuentas
    - Los administradores pueden actualizar cualquier cuenta
    """
    return cuenta_service.update_cuenta(
        db=db, 
        cuenta_id=cuenta_id, 
        cuenta_update=cuenta, 
        current_user=current_user
    )

@router.get("/generar/mesa/{mesa_id}", response_model=Dict[str, Any])
def generar_cuenta_mesa(
    mesa_id: int,
    db: Session = Depends(get_db),
    camarero: Usuario = Depends(get_camarero_actual)
):
    """
    Generar datos para una cuenta a partir de los pedidos de una mesa.
    No crea la cuenta en la base de datos, solo devuelve los datos calculados.
    """
    return cuenta_service.generar_cuenta_desde_pedidos(
        db=db,
        mesa_id=mesa_id,
        camarero_id=camarero.id
    )

@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cuenta(
    cuenta_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin_actual)
):
    """
    Eliminar una cuenta del sistema. Solo administradores pueden realizar esta acción.
    """
    cuenta_service.delete_cuenta(
        db=db,
        cuenta_id=cuenta_id,
        current_user=admin
    )
    return {} 