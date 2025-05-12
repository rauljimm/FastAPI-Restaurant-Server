"""
WebSocket endpoints.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from app.core.websockets import manager
from app.api.dependencies.auth import get_usuario_actual
from app.models.usuario import Usuario
from app.core.enums import RolUsuario
from fastapi.responses import JSONResponse
import jwt
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM

router = APIRouter(tags=["websockets"])

# Función auxiliar para verificar token WebSocket
async def verificar_token_websocket(token: str, roles_permitidos: list):
    """Verificar token y rol para conexiones WebSocket"""
    try:
        # Decodificar token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        rol = payload.get("rol")
        
        if not username or rol not in roles_permitidos:
            return False, "No autorizado"
            
        return True, rol
    except Exception as e:
        return False, str(e)

@router.websocket("/ws/cocina")
async def websocket_cocina(websocket: WebSocket, token: str = Query(...)):
    """Conexión WebSocket para el personal de la cocina (Cocineros y Administradores)"""
    # Verificar token antes de conectar
    autorizado, mensaje = await verificar_token_websocket(token, [RolUsuario.COCINERO, RolUsuario.ADMIN])
    
    if not autorizado:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=mensaje)
        return
        
    await manager.connect(websocket, "cocina")
    try:
        while True:
            # Esperar mensajes del cliente
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Mensaje recibido: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "cocina")

@router.websocket("/ws/camareros")
async def websocket_camareros(websocket: WebSocket, token: str = Query(...)):
    """Conexión WebSocket para los camareros (Camareros y Administradores)"""
    # Verificar token antes de conectar
    autorizado, mensaje = await verificar_token_websocket(token, [RolUsuario.CAMARERO, RolUsuario.ADMIN])
    
    if not autorizado:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=mensaje)
        return
        
    await manager.connect(websocket, "camareros")
    try:
        while True:
            # Esperar mensajes del cliente
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Mensaje recibido: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "camareros")

@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket, token: str = Query(...)):
    """Conexión WebSocket para los administradores"""
    # Verificar token antes de conectar
    autorizado, mensaje = await verificar_token_websocket(token, [RolUsuario.ADMIN])
    
    if not autorizado:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=mensaje)
        return
        
    await manager.connect(websocket, "admin")
    try:
        while True:
            # Esperar mensajes del cliente
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Mensaje recibido: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "admin") 