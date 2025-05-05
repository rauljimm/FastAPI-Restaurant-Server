"""
Gestión de conexiones WebSocket.
"""
import json
import asyncio
import logging
from typing import Dict, List, Any
from fastapi import WebSocket
from datetime import datetime, UTC

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("restaurante")

class ConnectionManager:
    """Gestiona las conexiones WebSocket para diferentes tipos de clientes"""
    
    def __init__(self):
        """Inicializa el administrador de conexiones con listas vacías para cada tipo de cliente"""
        self.active_connections: Dict[str, List[WebSocket]] = {
            "cocina": [],
            "camareros": [],
            "admin": []
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        """Acepta y almacena una nueva conexión WebSocket"""
        await websocket.accept()
        if client_type in self.active_connections:
            self.active_connections[client_type].append(websocket)
            logger.info(f"Nueva conexión WebSocket: {client_type}")

    def disconnect(self, websocket: WebSocket, client_type: str):
        """Elimina una conexión WebSocket"""
        if client_type in self.active_connections:
            if websocket in self.active_connections[client_type]:
                self.active_connections[client_type].remove(websocket)
                logger.info(f"Desconexión WebSocket: {client_type}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Envía un mensaje a un WebSocket específico"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_type: str):
        """Envía un mensaje a todos los WebSockets de un tipo de cliente específico"""
        if client_type in self.active_connections:
            for connection in self.active_connections[client_type]:
                await connection.send_text(message)
            
            # Registrar broadcast en logs
            try:
                msg_data = json.loads(message)
                logger.info(f"Mensaje enviado a {client_type}: {msg_data.get('tipo')}")
            except json.JSONDecodeError:
                logger.info(f"Mensaje enviado a {client_type}")

# Crear la instancia del administrador de conexiones
manager = ConnectionManager()

def log_event(message: str, level: str = "info"):
    """
    Registra eventos importantes en el log del sistema.
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    
    if level.lower() == "info":
        logger.info(f"{message}")
    elif level.lower() == "warning":
        logger.warning(f"{message}")
    elif level.lower() == "error":
        logger.error(f"{message}")
    elif level.lower() == "debug":
        logger.debug(f"{message}")
    
    # También imprimimos en consola para desarrollo
    print(f"[{timestamp}] {message}")

def safe_broadcast(message: Dict[str, Any], client_type: str):
    """
    Envía un mensaje a todos los clientes WebSocket de un tipo específico de manera segura.
    Funciona en ambos contextos sincrónicos y asincrónicos.
    """
    try:
        # Registrar el evento en logs
        tipo = message.get("tipo", "desconocido")
        if tipo == "actualizacion_pedido":
            log_event(f"Pedido #{message.get('pedido_id')}: cambio a {message.get('estado')} (Mesa: {message.get('mesa')})")
        elif tipo == "actualizacion_detalle":
            log_event(f"Detalle #{message.get('detalle_id')} del Pedido #{message.get('pedido_id')}: producto {message.get('producto')} cambió a {message.get('estado')}")
        elif tipo == "nueva_reserva":
            log_event(f"Nueva reserva #{message.get('reserva_id')} para {message.get('cliente')} en Mesa {message.get('mesa')}")
        
        # Intentar obtener el bucle en ejecución y crear una tarea
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(json.dumps(message), client_type))
    except RuntimeError:
        # Si no hay bucle en ejecución, simplemente pasa - estamos en un contexto de prueba o sincrónico
        pass 