"""
WebSocket endpoints.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websockets import manager
from app.api.dependencies.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(tags=["websockets"])

@router.websocket("/ws/cocina")
async def websocket_cocina(websocket: WebSocket):
    """WebSocket connection for kitchen staff"""
    await manager.connect(websocket, "cocina")
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            # Echo message back for now
            await manager.send_personal_message(f"Mensaje recibido: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "cocina")

@router.websocket("/ws/camareros")
async def websocket_camareros(websocket: WebSocket):
    """WebSocket connection for waiters"""
    await manager.connect(websocket, "camareros")
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            # Echo message back for now
            await manager.send_personal_message(f"Mensaje recibido: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "camareros")

@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """WebSocket connection for administrators"""
    await manager.connect(websocket, "admin")
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            # Echo message back for now
            await manager.send_personal_message(f"Mensaje recibido: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "admin") 