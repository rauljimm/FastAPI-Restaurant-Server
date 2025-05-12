"""
Servicio para operaciones de Cuenta.
"""
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, UTC, timedelta
import json

from app.models.cuenta import Cuenta
from app.models.mesa import Mesa
from app.models.usuario import Usuario
from app.models.pedido import Pedido, DetallePedido
from app.models.producto import Producto
from app.schemas.cuenta import CuentaCreate, CuentaUpdate
from app.core.enums import RolUsuario

def get_cuentas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    mesa_id: Optional[int] = None,
    camarero_id: Optional[int] = None,
    current_user: Usuario = None
) -> List[Cuenta]:
    """Obtener cuentas con filtros opcionales"""
    # Verificar permisos - solo administradores pueden ver todas las cuentas
    if current_user.rol != RolUsuario.ADMIN:
        # Si no es admin, solo puede ver sus propias cuentas
        camarero_id = current_user.id
    
    query = db.query(Cuenta)
    
    # Aplicar filtros
    if fecha_inicio is not None:
        query = query.filter(Cuenta.fecha_cobro >= fecha_inicio)
    
    if fecha_fin is not None:
        query = query.filter(Cuenta.fecha_cobro <= fecha_fin)
    
    if mesa_id is not None:
        query = query.filter(Cuenta.mesa_id == mesa_id)
    
    if camarero_id is not None:
        query = query.filter(Cuenta.camarero_id == camarero_id)
    
    # Ordenar por fecha de cobro (últimos primero)
    query = query.order_by(desc(Cuenta.fecha_cobro))
    
    cuentas = query.offset(skip).limit(limit).all()
    
    # Procesar el campo detalles para cada cuenta
    for cuenta in cuentas:
        cuenta.detalles = process_detalles_field(cuenta.detalles)
    
    return cuentas

def get_cuenta_by_id(db: Session, cuenta_id: int, current_user: Usuario = None) -> Cuenta:
    """Obtener una cuenta específica por ID"""
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    # Verificar permisos
    if current_user.rol != RolUsuario.ADMIN and cuenta.camarero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para ver esta cuenta"
        )
    
    # Procesar el campo detalles
    cuenta.detalles = process_detalles_field(cuenta.detalles)
    
    return cuenta

def process_detalles_field(detalles_field):
    """Procesa el campo detalles para convertirlo en un array JSON válido"""
    if detalles_field is None:
        return []
    
    # Si ya es una lista, devolverla directamente
    if isinstance(detalles_field, list):
        return detalles_field
    
    # Si es un string, intentar parsearlo como JSON
    if isinstance(detalles_field, str):
        try:
            if detalles_field.strip():  # Si no está vacío
                parsed_detalles = json.loads(detalles_field)
                
                # Si el resultado es una lista, devolverla
                if isinstance(parsed_detalles, list):
                    return parsed_detalles
                
                # Si el resultado es un objeto, envolverlo en una lista
                if isinstance(parsed_detalles, dict):
                    return [parsed_detalles]
                
                # Si no es ni lista ni objeto, devolver lista vacía
                return []
            else:
                return []
        except json.JSONDecodeError:
            print(f"Error al decodificar JSON: {detalles_field}")
            return []
    
    # Por defecto, devolver lista vacía
    return []

def create_cuenta(
    db: Session,
    cuenta: CuentaCreate,
    camarero_id: int
) -> Cuenta:
    """Crear una nueva cuenta"""
    # Verificar que el camarero existe
    camarero = db.query(Usuario).filter(Usuario.id == camarero_id).first()
    if camarero is None:
        raise HTTPException(status_code=404, detail="Camarero no encontrado")
    
    # Verificar que la mesa existe (si se especifica)
    mesa = None
    if cuenta.mesa_id:
        mesa = db.query(Mesa).filter(Mesa.id == cuenta.mesa_id).first()
        if mesa is None:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
    
    # Convertir lista de detalles a JSON
    detalles_json = json.dumps([item.model_dump() for item in cuenta.detalles])
    
    # Crear la nueva cuenta
    db_cuenta = Cuenta(
        mesa_id=cuenta.mesa_id,
        numero_mesa=cuenta.numero_mesa,
        camarero_id=camarero_id,
        nombre_camarero=cuenta.nombre_camarero,
        total=cuenta.total,
        metodo_pago=cuenta.metodo_pago,
        detalles=detalles_json
    )
    
    db.add(db_cuenta)
    db.commit()
    db.refresh(db_cuenta)
    
    # Deserializar detalles antes de devolver
    db_cuenta.detalles = process_detalles_field(db_cuenta.detalles)
    
    return db_cuenta

def update_cuenta(
    db: Session,
    cuenta_id: int,
    cuenta_update: CuentaUpdate,
    current_user: Usuario
) -> Cuenta:
    """Actualizar una cuenta existente"""
    db_cuenta = get_cuenta_by_id(db, cuenta_id, current_user)
    
    # Solo se permite actualizar el método de pago
    if cuenta_update.metodo_pago is not None:
        db_cuenta.metodo_pago = cuenta_update.metodo_pago
    
    db.commit()
    db.refresh(db_cuenta)
    
    # Deserializar detalles antes de devolver
    db_cuenta.detalles = process_detalles_field(db_cuenta.detalles)
    
    return db_cuenta

def get_resumen_cuentas(
    db: Session,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    current_user: Usuario = None
) -> Dict[str, Any]:
    """Obtener resumen de ingresos en un período"""
    # Verificar permisos - solo administradores pueden ver el resumen
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden ver el resumen de ingresos"
        )
    
    # Si no se especifica fecha_inicio, usar hace 30 días
    if fecha_inicio is None:
        fecha_inicio = datetime.now(UTC) - timedelta(days=30)
    
    # Si no se especifica fecha_fin, usar ahora
    if fecha_fin is None:
        fecha_fin = datetime.now(UTC)
    
    # Query base
    query = db.query(Cuenta).filter(
        Cuenta.fecha_cobro >= fecha_inicio,
        Cuenta.fecha_cobro <= fecha_fin
    )
    
    # Calcular total de ingresos
    total_ingresos = sum(cuenta.total for cuenta in query.all())
    
    # Contar cuentas
    total_cuentas = query.count()
    
    # Obtener promedio por cuenta
    promedio_por_cuenta = total_ingresos / total_cuentas if total_cuentas > 0 else 0
    
    # Agrupar por camarero para ver rendimiento
    ingresos_por_camarero = {}
    for cuenta in query.all():
        if cuenta.nombre_camarero in ingresos_por_camarero:
            ingresos_por_camarero[cuenta.nombre_camarero]["total"] += cuenta.total
            ingresos_por_camarero[cuenta.nombre_camarero]["cuentas"] += 1
        else:
            ingresos_por_camarero[cuenta.nombre_camarero] = {
                "total": cuenta.total,
                "cuentas": 1
            }
    
    # Calcular promedios por camarero
    for camarero, datos in ingresos_por_camarero.items():
        datos["promedio"] = datos["total"] / datos["cuentas"]
    
    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_ingresos": total_ingresos,
        "total_cuentas": total_cuentas,
        "promedio_por_cuenta": promedio_por_cuenta,
        "ingresos_por_camarero": ingresos_por_camarero
    }

def generar_cuenta_desde_pedidos(
    db: Session,
    mesa_id: int,
    camarero_id: int
) -> Dict[str, Any]:
    """Generar datos para una cuenta a partir de los pedidos de una mesa"""
    try:
        # Verificar que la mesa existe
        mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
        if mesa is None:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        
        # Verificar que el camarero existe
        camarero = db.query(Usuario).filter(Usuario.id == camarero_id).first()
        if camarero is None:
            raise HTTPException(status_code=404, detail="Camarero no encontrado")
        
        # Obtener todos los pedidos activos de la mesa
        pedidos = db.query(Pedido).filter(
            Pedido.mesa_id == mesa_id,
            Pedido.estado != "cancelado"
        ).all()
        
        # Calcular total y preparar detalles
        total = 0
        detalles = []
        
        # Si no hay pedidos, devolver una cuenta vacía pero válida
        if not pedidos:
            print(f"No hay pedidos activos para la mesa {mesa_id}")
            datos_cuenta = {
                "mesa_id": mesa_id,
                "numero_mesa": mesa.numero,
                "camarero_id": camarero_id,
                "nombre_camarero": f"{camarero.nombre} {camarero.apellido}",
                "total": 0,
                "detalles": []
            }
            return datos_cuenta
        
        for pedido in pedidos:
            # Verificar que el pedido tenga detalles
            if not pedido.detalles:
                continue
                
            # Obtener detalles del pedido
            for detalle in pedido.detalles:
                producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
                if producto:
                    item = {
                        "pedido_id": pedido.id,
                        "producto_id": producto.id,
                        "nombre_producto": producto.nombre,
                        "cantidad": detalle.cantidad,
                        "precio_unitario": detalle.precio_unitario,
                        "subtotal": detalle.subtotal,
                        "observaciones": detalle.observaciones
                    }
                    detalles.append(item)
                    total += detalle.subtotal
        
        # Preparar datos para la cuenta
        datos_cuenta = {
            "mesa_id": mesa_id,
            "numero_mesa": mesa.numero,
            "camarero_id": camarero_id,
            "nombre_camarero": f"{camarero.nombre} {camarero.apellido}",
            "total": total,
            "detalles": detalles
        }
        
        return datos_cuenta
    except Exception as e:
        # Registrar la excepción para debugging
        print(f"Error en generar_cuenta_desde_pedidos: {str(e)}")
        # Devolver una cuenta vacía pero válida en caso de error
        return {
            "mesa_id": mesa_id,
            "numero_mesa": 0,  # Valor por defecto
            "camarero_id": camarero_id,
            "nombre_camarero": "Error al generar cuenta",
            "total": 0,
            "detalles": []
        }

def delete_cuenta(db: Session, cuenta_id: int, current_user: Usuario) -> None:
    """Eliminar una cuenta por su ID"""
    # Obtener la cuenta y verificar permisos
    db_cuenta = get_cuenta_by_id(db, cuenta_id, current_user)
    
    # Solo admin puede eliminar cuentas
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden eliminar cuentas"
        )
    
    # Eliminar la cuenta
    db.delete(db_cuenta)
    db.commit()
    
    return None 